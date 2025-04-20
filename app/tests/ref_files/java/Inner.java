// Primitive types
int count;
float rate;
double average;
boolean isActive;
char grade;
byte level;
short temperature;
long timestamp;

// Access modifiers and static/final
public int publicInt;
private static String staticString;
protected final double finalDouble = 3.14;
public static final int MAX_VALUE = 1000;
static final boolean FLAG = true;

// Object references
String name;
List<String> names;
Map<String, Integer> scores;

// Arrays
int[] numbers;
String[][] namesMatrix;

// Initialized fields
int id = 1;
String status = "active";
List<Integer> values = new ArrayList<>();

// Transient and volatile
transient int sessionData;
volatile boolean updated;

// Generic types
List<?> wildcardList;
Map<String, ? extends Number> numberMap;

// Complex initializations
Map<String, List<Integer>> nestedMap = new HashMap<>();
List<Map<String, Set<Double>>> complexList = new ArrayList<>();

// With annotations
@Deprecated
String deprecatedField;

@SuppressWarnings("unused")
private int hidden = 42;

// Final with initialization block
final String fixed = "constant";

// Static block variables (not fields but test parser scope)
static {
    int staticBlockTemp = 5;
    String msg = "Hello";
}

// Inner class variables
class Inner {
    int innerCount;
    private List<String> innerList = new ArrayList<>();
}

