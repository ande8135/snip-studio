import java.io.File;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.*;
import org.jf.dexlib2.iface.instruction.Instruction;

public class Dump {
    public static void main(String[] a) throws Exception {
        DexFile dex = new org.jf.dexlib2.dexbacked.DexBackedDexFile(Opcodes.forApi(29), java.nio.file.Files.readAllBytes(new File(a[0]).toPath()));
        for (ClassDef c : dex.getClasses()) {
            System.out.println(c.getType() + " extends " + c.getSuperclass() + " " + c.getInterfaces());
            for (Method m : c.getMethods()) {
                MethodImplementation impl = m.getImplementation();
                int n = 0; if (impl != null) for (Instruction i : impl.getInstructions()) n++;
                System.out.println("   " + m.getName() + m.getParameterTypes() + m.getReturnType() + " regs=" + (impl == null ? "-" : impl.getRegisterCount()) + " insns=" + n
                    + " tries=" + (impl == null ? 0 : impl.getTryBlocks().size()) + " annos=" + m.getAnnotations().size());
            }
        }
    }
}
