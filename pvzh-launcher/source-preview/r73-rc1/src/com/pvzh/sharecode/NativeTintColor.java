package com.pvzh.sharecode;

import java.io.IOException;

/** Deterministic straight-RGBA colorization; no scaling, alpha change or accumulation. */
public final class NativeTintColor {
    public static final String ALGORITHM="max-channel-tint-v1";
    private NativeTintColor(){}
    public static byte[] apply(byte[] original,int rgb,int strengthPermille)throws IOException{
        if(original==null||original.length%4!=0||original.length>32*1024*1024)throw new IOException("调色RGBA长度无效");
        if(rgb<0||rgb>0xffffff||strengthPermille<0||strengthPermille>1000)throw new IOException("调色颜色或强度无效");
        byte[] result=original.clone();if(strengthPermille==0)return result;
        int[] color={(rgb>>>16)&255,(rgb>>>8)&255,rgb&255};
        for(int at=0;at<original.length;at+=4){
            if((original[at+3]&255)==0)continue;
            int brightness=Math.max(original[at]&255,Math.max(original[at+1]&255,original[at+2]&255));
            for(int channel=0;channel<3;channel++){
                int source=original[at+channel]&255;
                long numerator=(long)source*255*(1000-strengthPermille)+(long)color[channel]*brightness*strengthPermille;
                result[at+channel]=(byte)((numerator+127500)/255000);
            }
        }
        return result;
    }
}
