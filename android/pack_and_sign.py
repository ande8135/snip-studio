"""Assemble an aligned APK and sign it with APK Signature Scheme v2.

Usage: python3 pack_and_sign.py base.apk classes.dex assets_dir key.pem out.apk
"""

import datetime
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

ALIGN_EXTRA_ID = 0xD935  # same marker zipalign uses
V2_BLOCK_ID = 0x7109871A
SIG_RSA_PKCS1_SHA256 = 0x0103
CHUNK = 1024 * 1024


# ---------- packaging ----------
def write_aligned(out: Path, entries: list[tuple[str, bytes, bool]]) -> None:
    """entries: (name, data, store_uncompressed). Stored entries get 4-byte aligned data."""
    with zipfile.ZipFile(out, "w") as zf:
        for name, data, store in entries:
            info = zipfile.ZipInfo(name, date_time=(1981, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if store else zipfile.ZIP_DEFLATED
            info.create_system = 0
            if store:
                header_end = zf.fp.tell() + 30 + len(name.encode())
                pad = (-(header_end + 6)) % 4
                info.extra = struct.pack("<HHH", ALIGN_EXTRA_ID, 2 + pad, 4) + b"\0" * pad
            zf.writestr(info, data)


# ---------- v2 signing ----------
def lp(b: bytes) -> bytes:  # uint32 length-prefixed
    return struct.pack("<I", len(b)) + b


def find_eocd(data: bytes) -> int:
    pos = data.rfind(b"PK\x05\x06")
    if pos < 0:
        raise ValueError("no end of central directory")
    return pos


def chunked_digest(sections: list[bytes]) -> bytes:
    digests = []
    for sec in sections:
        for i in range(0, len(sec), CHUNK):
            chunk = sec[i : i + CHUNK]
            digests.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(chunk)) + chunk).digest())
    return hashlib.sha256(b"\x5a" + struct.pack("<I", len(digests)) + b"".join(digests)).digest()


def load_or_make_key(path: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    if path.exists():
        pem = path.read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        cert = x509.load_pem_x509_certificate(pem)
        return key, cert
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Snip Studio"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Snip Studio"),
        ]
    )
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365 * 30))
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        + cert.public_bytes(serialization.Encoding.PEM)
    )
    return key, cert


def sign_v2(apk: bytes, key: rsa.RSAPrivateKey, cert: x509.Certificate) -> bytes:
    eocd = find_eocd(apk)
    cd_size, cd_off = struct.unpack_from("<II", apk, eocd + 12)
    if cd_off + cd_size != eocd:
        raise ValueError("unexpected zip layout")
    entries, cd, tail = apk[:cd_off], apk[cd_off:eocd], apk[eocd:]

    digest = chunked_digest([entries, cd, tail])  # EOCD's CD offset already equals the block's future offset
    signed_data = (
        lp(lp(struct.pack("<I", SIG_RSA_PKCS1_SHA256) + lp(digest)))
        + lp(lp(cert.public_bytes(serialization.Encoding.DER)))
        + lp(b"")
    )
    signature = key.sign(signed_data, padding.PKCS1v15(), hashes.SHA256())
    pubkey = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    signer = lp(signed_data) + lp(lp(struct.pack("<I", SIG_RSA_PKCS1_SHA256) + lp(signature))) + lp(pubkey)
    value = lp(lp(signer))

    pair = struct.pack("<QI", 4 + len(value), V2_BLOCK_ID) + value
    block_size = len(pair) + 8 + 16  # pairs + trailing size + magic
    block = struct.pack("<Q", block_size) + pair + struct.pack("<Q", block_size) + b"APK Sig Block 42"

    new_tail = bytearray(tail)
    struct.pack_into("<I", new_tail, 16, cd_off + len(block))
    return entries + block + cd + bytes(new_tail)


def verify_v2(apk: bytes) -> str:
    """Independent re-check: parse the block, recompute the digest, verify the signature."""
    eocd = find_eocd(apk)
    cd_size, cd_off = struct.unpack_from("<II", apk, eocd + 12)
    assert apk[cd_off - 16 : cd_off] == b"APK Sig Block 42", "magic missing"
    size = struct.unpack_from("<Q", apk, cd_off - 24)[0]
    start = cd_off - size - 8
    assert struct.unpack_from("<Q", apk, start)[0] == size, "block size mismatch"
    pos, found = start + 8, None
    while pos < cd_off - 24:
        ln, pid = struct.unpack_from("<QI", apk, pos)
        if pid == V2_BLOCK_ID:
            found = apk[pos + 12 : pos + 8 + ln]
        pos += 8 + ln
    assert found, "no v2 block"

    def rd(buf: bytes, p: int) -> tuple[bytes, int]:
        n = struct.unpack_from("<I", buf, p)[0]
        return buf[p + 4 : p + 4 + n], p + 4 + n

    signers, _ = rd(found, 0)
    signer, _ = rd(signers, 0)
    signed_data, p = rd(signer, 0)
    sigs, p = rd(signer, p)
    pub, _ = rd(signer, p)
    sig_item, _ = rd(sigs, 0)
    algo = struct.unpack_from("<I", sig_item, 0)[0]
    sig, _ = rd(sig_item, 4)
    pk = serialization.load_der_public_key(pub)
    pk.verify(sig, signed_data, padding.PKCS1v15(), hashes.SHA256())
    digests, q = rd(signed_data, 0)
    certs, _ = rd(signed_data, q)
    d_item, _ = rd(digests, 0)
    stored_digest, _ = rd(d_item, 4)
    cert_der, _ = rd(certs, 0)
    cert = x509.load_der_x509_certificate(cert_der)
    assert (
        cert.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        == pub
    ), "cert/key mismatch"
    tail = bytearray(apk[eocd:])
    struct.pack_into("<I", tail, 16, start)
    assert chunked_digest([apk[:start], apk[cd_off:eocd], bytes(tail)]) == stored_digest, "digest mismatch"
    return f"v2 signature OK (alg 0x{algo:04x}, cert SHA-256 {hashlib.sha256(cert_der).hexdigest()[:16]}…)"


def check_alignment(apk_path: Path) -> None:
    with zipfile.ZipFile(apk_path) as zf, open(apk_path, "rb") as f:
        for info in zf.infolist():
            if info.compress_type == zipfile.ZIP_STORED:
                f.seek(info.header_offset + 26)
                n, m = struct.unpack("<HH", f.read(4))
                data_off = info.header_offset + 30 + n + m
                assert data_off % 4 == 0, f"{info.filename} not aligned"
        assert zf.getinfo("resources.arsc").compress_type == zipfile.ZIP_STORED
        assert zf.testzip() is None


def main() -> None:
    base, dex, assets, key_path, out = map(Path, sys.argv[1:6])
    entries: list[tuple[str, bytes, bool]] = []
    with zipfile.ZipFile(base) as zf:
        for info in zf.infolist():
            data = zf.read(info)
            store = info.filename == "resources.arsc" or info.filename.endswith(".png")
            entries.append((info.filename, data, store))
    entries.insert(1, ("classes.dex", dex.read_bytes(), False))
    for f in sorted(p for p in assets.rglob("*") if p.is_file()):
        entries.append(("assets/" + f.relative_to(assets).as_posix(), f.read_bytes(), False))

    unsigned = out.with_suffix(".unsigned.apk")
    write_aligned(unsigned, entries)
    key, cert = load_or_make_key(key_path)
    signed = sign_v2(unsigned.read_bytes(), key, cert)
    out.write_bytes(signed)
    unsigned.unlink()
    check_alignment(out)
    print(verify_v2(signed))
    print(f"wrote {out} ({len(signed):,} bytes)")


if __name__ == "__main__":
    main()
