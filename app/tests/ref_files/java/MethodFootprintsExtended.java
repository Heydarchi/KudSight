// Basic Methods
void simpleMethod() {}
int getNumber() { return 0; }
String getName(String input) { return input; }
boolean isAvailable() { return true; }

// Modifiers and Return Types
public static void log(String msg) {}
private final int calculate(int a, int b) { return a + b; }
protected synchronized void access() {}
static native int nativeMethod();
transient void notValidModifier(); // Invalid use of modifier, test edge case

// Parameters and Varargs
void methodWithMultipleParams(int a, String b, double c) {}
void methodWithArrayParam(String[] items) {}
void methodWithVarargs(String... args) {}
void methodWith2DArrayParam(int[][] matrix) {}
void methodWithFinalParam(final int x) {}

// Throws Clause
void riskyMethod() throws IOException {}
void multiException() throws IOException, SQLException {}

// Generics
<T> T genericMethod(T input) { return input; }
<U, V> Map<U, V> mapMethod(List<U> list, V value) { return null; }
List<String> getList() { return new ArrayList<>(); }
public static <T extends Comparable<T>> T max(T a, T b) { return a.compareTo(b) > 0 ? a : b; }

// Annotations
@Override
public String toString() { return "text"; }

@Deprecated
void oldMethod() {}

@SuppressWarnings("unchecked")
public <T> List<T> unsafeCast(Object obj) { return (List<T>) obj; }

// Interface Methods
interface MyInterface {
    void doWork();
    int calculate(int a, int b);
}

// Abstract Methods
abstract class AbstractWorker {
    abstract void run();
    abstract int compute(String data);
}

// Constructors
public MyClass() {}
private MyClass(int x) {}
protected MyClass(String name, int age) {}

// Enums and Static Blocks
enum Color {
    RED, GREEN, BLUE;

    void printColor() {}
}

// Inner Classes and Anonymous Classes
class Outer {
    class Inner {
        void innerMethod() {}
    }

    void anonymous() {
        Runnable r = new Runnable() {
            @Override
            public void run() {}
        };
    }
}

// Lambdas and Method References (not valid footprints but test parser tolerance)
Runnable r = () -> {};
Function<String, Integer> parser = Integer::parseInt;

// Extra combinations
public <T> void process(List<? extends T> items) {}
private <T extends Number> double sum(List<T> numbers) { return 0; }
static <K, V> Map<K, V> newMap() { return new HashMap<>(); }
public static final <E> void shuffle(List<E> list) {}

