package com.pvzh.sharecode;

/** Session-owned paper-doll form state. Rendering a control never writes this state. */
final class NativeArtworkParameters {
    static final String SCALE="scale",X="x",Y="y";
    private String session;
    private double scale=100,x=0,y=2;
    boolean belongsTo(String value){return value!=null&&value.equals(session);}
    void load(String value,double percent,double horizontal,double vertical){
        if(value==null||value.isEmpty())throw new IllegalArgumentException("缺少当前美术会话");
        if(belongsTo(value))return;
        validate(percent,horizontal,vertical);session=value;scale=percent;x=horizontal;y=vertical;
    }
    void clear(){session=null;scale=100;x=0;y=2;}
    double value(String field){if(SCALE.equals(field))return scale;if(X.equals(field))return x;if(Y.equals(field))return y;throw new IllegalArgumentException("未知位置参数");}
    double ppu(){return 7500.0/scale;}
    void set(String field,double value){setValues(SCALE.equals(field)?value:scale,X.equals(field)?value:x,Y.equals(field)?value:y);}
    void setValues(double percent,double horizontal,double vertical){validate(percent,horizontal,vertical);scale=percent;x=horizontal;y=vertical;}
    void reset(){setValues(100,0,2);}
    static int maximum(String field){return SCALE.equals(field)?4900:4000;}
    static double minimum(String field){return SCALE.equals(field)?10:-20;}
    static double step(String field){return SCALE.equals(field)?.1:.01;}
    int progress(String field){return Math.max(0,Math.min(maximum(field),(int)Math.round((value(field)-minimum(field))/step(field))));}
    static double atProgress(String field,int progress){if(progress<0||progress>maximum(field))throw new IllegalArgumentException("滑条位置超出范围");return Math.rint((minimum(field)+progress*step(field))*1000)/1000;}
    private static void validate(double percent,double horizontal,double vertical){
        if(!Double.isFinite(percent)||percent<10||percent>500||!Double.isFinite(horizontal)||horizontal< -20||horizontal>20||!Double.isFinite(vertical)||vertical< -20||vertical>20)throw new IllegalArgumentException("大小需10～500%，左右和上下位置需-20～20");
    }
}
