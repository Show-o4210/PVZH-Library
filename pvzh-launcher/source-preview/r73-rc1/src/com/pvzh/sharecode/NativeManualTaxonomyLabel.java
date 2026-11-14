package com.pvzh.sharecode;

/** Display-only labels; the raw value remains the selector key and saved value. */
final class NativeManualTaxonomyLabel {
    static String choice(String name,String value){
        if(value==null)throw new IllegalArgumentException("Selector value required");
        if(name==null||name.isEmpty()||name.equals(value))return value;
        return name+"\n"+value;
    }
    static String annotated(String value,String note){
        if(value==null)throw new IllegalArgumentException("Selector value required");
        return note==null||note.isEmpty()?value:value+"\n"+note;
    }
    private NativeManualTaxonomyLabel(){}
}
