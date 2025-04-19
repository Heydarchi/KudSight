package com.kudsight.samples;

import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * This is a class comment that demonstrates how comments
 * are handled by the analyzer
 */
public class ComplexGenerics<T extends Comparable<T>, U> {
    
    // Class fields with various types
    private Map<String, List<T>> dataMap;
    private U auxiliaryData;
    protected static final int MAX_SIZE = 100;
    public List<Function<T, U>> transformers;
    
    // Constructor with generics
    public ComplexGenerics(Collection<T> initialData, U auxData) {
        this.dataMap = new HashMap<>();
        this.auxiliaryData = auxData;
        this.transformers = new ArrayList<>();
        
        // Process initial data
        if (initialData != null) {
            processInitialData(initialData);
        }
    }
    
    // Method with generic parameters and return type
    public <V> Map<String, V> processData(List<T> inputs, Function<T, V> transformer) {
        Map<String, V> result = new HashMap<>();
        
        for (T input : inputs) {
            V transformed = transformer.apply(input);
            result.put(input.toString(), transformed);
        }
        
        return result;
    }
    
    // Private helper method
    private void processInitialData(Collection<T> data) {
        dataMap.put("initial", new ArrayList<>(data));
    }
    
    // Inner class with its own generic parameter
    /* This is a comment before the inner class declaration */
    public static class DataProcessor<R> {
        private Function<Object, R> processor;
        
        public DataProcessor(Function<Object, R> processor) {
            this.processor = processor;
        }
        
        public R process(Object input) {
            return processor.apply(input);
        }
    }
    
    // Interface definition with generics
    public interface DataTransformer<I, O> {
        O transform(I input);
        List<O> transformBatch(List<I> inputs);
    }
}

// Additional class in the same file
class StringProcessor extends ComplexGenerics<String, Integer> implements ComplexGenerics.DataTransformer<String, Integer> {
    
    public StringProcessor() {
        super(Collections.emptyList(), 0);
    }
    
    @Override
    public Integer transform(String input) {
        return input.length();
    }
    
    @Override
    public List<Integer> transformBatch(List<String> inputs) {
        return inputs.stream()
                .map(this::transform)
                .collect(Collectors.toList());
    }
}
