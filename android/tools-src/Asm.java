import java.io.File;
import brut.directory.ExtFile;
import brut.androlib.src.SmaliBuilder;

public class Asm {
    public static void main(String[] a) throws Exception {
        SmaliBuilder.build(new ExtFile(new File(a[0])), new File(a[1]), Integer.parseInt(a[2]));
        System.out.println("assembled " + a[1]);
    }
}
