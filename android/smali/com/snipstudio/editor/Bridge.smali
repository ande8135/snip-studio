.class public Lcom/snipstudio/editor/Bridge;
.super Ljava/lang/Object;

.field private act:Lcom/snipstudio/editor/MainActivity;

.method public constructor <init>(Lcom/snipstudio/editor/MainActivity;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/snipstudio/editor/Bridge;->act:Lcom/snipstudio/editor/MainActivity;
    return-void
.end method

.method public saveImage(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 10
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    :try_start
    const/4 v0, 0x0
    invoke-static {p1, v0}, Landroid/util/Base64;->decode(Ljava/lang/String;I)[B
    move-result-object v0
    new-instance v1, Landroid/content/ContentValues;
    invoke-direct {v1}, Landroid/content/ContentValues;-><init>()V
    const-string v2, "_display_name"
    invoke-virtual {v1, v2, p2}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V
    const-string v2, "mime_type"
    invoke-virtual {v1, v2, p3}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V
    const-string v2, "relative_path"
    const-string v3, "Pictures/Snip Studio"
    invoke-virtual {v1, v2, v3}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V
    iget-object v2, p0, Lcom/snipstudio/editor/Bridge;->act:Lcom/snipstudio/editor/MainActivity;
    invoke-virtual {v2}, Lcom/snipstudio/editor/MainActivity;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v2
    sget-object v3, Landroid/provider/MediaStore$Images$Media;->EXTERNAL_CONTENT_URI:Landroid/net/Uri;
    invoke-virtual {v2, v3, v1}, Landroid/content/ContentResolver;->insert(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;
    move-result-object v3
    if-eqz v3, :fail
    invoke-virtual {v2, v3}, Landroid/content/ContentResolver;->openOutputStream(Landroid/net/Uri;)Ljava/io/OutputStream;
    move-result-object v4
    invoke-virtual {v4, v0}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {v4}, Ljava/io/OutputStream;->close()V
    const-string v5, "ok"
    return-object v5
    :fail
    const-string v5, "could not create the file"
    return-object v5
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :err
    :err
    move-exception v0
    invoke-virtual {v0}, Ljava/lang/Throwable;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method
