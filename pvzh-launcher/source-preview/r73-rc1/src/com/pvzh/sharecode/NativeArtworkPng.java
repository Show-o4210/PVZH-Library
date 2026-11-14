package com.pvzh.sharecode;

import java.io.*;
import java.util.*;
import java.util.zip.*;

/** Lossless 8-bit non-interlaced PNG pixels. Android Bitmaps are preview-only. */
public final class NativeArtworkPng {
    private static final byte[] SIGNATURE={(byte)137,80,78,71,13,10,26,10};
    private static final int IHDR=0x49484452,PLTE=0x504c5445,TRNS=0x74524e53,IDAT=0x49444154,IEND=0x49454e44;
    private static final int ACTL=0x6163544c,FCTL=0x6663544c,FDAT=0x66644154;
    public static final int MAX_PNG=32*1024*1024,MAX_SIDE=4096;
    public static final class Image {public final int width,height;public final byte[] rgba;Image(int w,int h,byte[] pixels){width=w;height=h;rgba=pixels;}}
    private NativeArtworkPng(){}
    private static void need(boolean yes,String reason)throws IOException{if(!yes)throw new IOException("PNG不支持："+reason);}
    private static int int32(byte[] bytes,int offset){return (bytes[offset]&255)<<24|(bytes[offset+1]&255)<<16|(bytes[offset+2]&255)<<8|bytes[offset+3]&255;}
    private static int u32(byte[] bytes,int offset)throws IOException{need(offset>=0&&offset+4<=bytes.length,"数据不完整");long value=((bytes[offset]&255L)<<24)|((bytes[offset+1]&255L)<<16)|((bytes[offset+2]&255L)<<8)|(bytes[offset+3]&255L);need(value<=Integer.MAX_VALUE,"长度越界");return(int)value;}
    private static int u16(byte[] b,int p){return((b[p]&255)<<8)|(b[p+1]&255);}
    private static int paeth(int a,int b,int c){int p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;}
    public static Image decode(byte[] png)throws Exception{return decode(png,-1,-1);}
    public static Image decode(byte[] png,int expectedWidth,int expectedHeight)throws Exception{
        need(png!=null&&png.length>=33&&png.length<=MAX_PNG,"文件需在32MiB以内");for(int i=0;i<8;i++)need(png[i]==SIGNATURE[i],"只接受PNG文件");
        int p=8,width=0,height=0,color=-1,channels=0,firstIdat=-1,endIdat=-1;
        boolean header=false,idatClosed=false,end=false;
        byte[] palette=null,transparency=null;
        CRC32 crc=new CRC32();
        while(p<png.length){need(p+12<=png.length,"区块不完整");int length=u32(png,p);need(length<=png.length-p-12,"区块长度越界");
            int type=int32(png,p+4);for(int i=0;i<4;i++)need((png[p+4+i]>='A'&&png[p+4+i]<='Z')||(png[p+4+i]>='a'&&png[p+4+i]<='z'),"区块名称无效");
            crc.reset();crc.update(png,p+4,4+length);
            need(crc.getValue()==(int32(png,p+8+length)&0xffffffffL),"区块校验失败");int data=p+8;
            if(!header)need(type==IHDR&&length==13,"首区块必须为IHDR");
            if(type==IHDR){need(!header&&p==8&&length==13,"IHDR重复或结构无效");width=u32(png,data);height=u32(png,data+4);need(width>=1&&height>=1&&width<=MAX_SIDE&&height<=MAX_SIDE,"宽高需1～4096");need(expectedWidth<0||width==expectedWidth&&height==expectedHeight,"尺寸必须与原图完全相同，不自动缩放");need(png[data+8]==8,"首期只支持8位PNG");color=png[data+9]&255;channels=color==0||color==3?1:color==2?3:color==4?2:color==6?4:0;need(channels>0,"颜色类型不支持");need(png[data+10]==0&&png[data+11]==0&&png[data+12]==0,"首期不支持交错或特殊压缩PNG");header=true;}
            else if(type==PLTE){need(firstIdat<0&&palette==null&&length>=3&&length<=768&&length%3==0,"调色板无效");palette=Arrays.copyOfRange(png,data,data+length);}
            else if(type==TRNS){need(firstIdat<0&&transparency==null,"透明信息重复或位置无效");need(color==0&&length==2||color==2&&length==6||color==3&&palette!=null&&length<=palette.length/3,"透明信息与颜色类型不一致");transparency=Arrays.copyOfRange(png,data,data+length);if(color==0)need(u16(transparency,0)<=255,"灰度透明值越界");if(color==2)for(int i=0;i<6;i+=2)need(u16(transparency,i)<=255,"RGB透明值越界");}
            else if(type==IDAT){
                need(!idatClosed,"IDAT区块必须连续");need(color!=3||palette!=null,"索引PNG缺少调色板");
                if(firstIdat<0)firstIdat=p;
                endIdat=p+12+length;
            }
            else if(type==IEND){need(firstIdat>=0&&length==0&&p+12==png.length,"IEND缺失、无像素或含尾随数据");end=true;break;}
            else {need(type!=ACTL&&type!=FCTL&&type!=FDAT,"不支持动画PNG");need((png[p+4]&32)!=0,"未知关键区块");if(firstIdat>=0)idatClosed=true;}
            p+=12+length;
        }
        need(header&&firstIdat>=0&&end,"PNG结构不完整");
        byte[] current=new byte[1+width*channels],previous=new byte[current.length],pixels;
        try{pixels=new byte[width*height*4];}
        catch(OutOfMemoryError exhausted){throw new IOException("PNG像素内存不足，请使用尺寸较小的图片",exhausted);}
        try(Idat input=new Idat(png,firstIdat,endIdat)){
            for(int y=0;y<height;y++){
                input.readRow(current);
                unfilter(current,previous,channels);
                writeRow(current,pixels,y*width*4,color,channels,palette,transparency);
                byte[] swap=previous;previous=current;current=swap;
            }
            input.finish(current);
        }catch(DataFormatException invalid){throw new IOException("PNG像素压缩流无效",invalid);}
        return new Image(width,height,pixels);
    }
    /** Walks the already validated contiguous IDAT run without copying any payload. */
    private static final class Idat implements AutoCloseable{
        private final byte[] png;
        private final int end;
        private final Inflater inflater=new Inflater();
        private int cursor;
        Idat(byte[] png,int start,int end){this.png=png;cursor=start;this.end=end;}
        private void feed(){
            while(cursor<end){
                int length=int32(png,cursor),data=cursor+8;
                cursor+=12+length;
                if(length==0)continue;
                inflater.setInput(png,data,length);
                return;
            }
        }
        void readRow(byte[] row)throws IOException,DataFormatException{
            int offset=0;
            while(offset<row.length){
                if(inflater.needsInput())feed();
                int count=inflater.inflate(row,offset,row.length-offset);
                if(count>0){offset+=count;continue;}
                need(!inflater.finished()&&inflater.needsInput()&&cursor<end,"像素数据长度不符或压缩流未结束");
            }
        }
        void finish(byte[] probe)throws IOException,DataFormatException{
            while(!inflater.finished()){
                if(inflater.needsInput())feed();
                need(inflater.inflate(probe,0,1)==0,"像素解压长度超出尺寸");
                need(inflater.finished()||inflater.needsInput()&&cursor<end,"像素压缩流无效或未结束");
            }
            need(inflater.getRemaining()==0,"像素数据含额外压缩流");
            for(;cursor<end;cursor+=12)need(int32(png,cursor)==0,"像素数据含额外压缩流");
        }
        @Override public void close(){inflater.end();}
    }
    private static void unfilter(byte[] row,byte[] previous,int channels)throws IOException{
        int filter=row[0]&255;
        need(filter<=4,"滤镜类型无效");
        if(filter==0)return;
        for(int i=1;i<row.length;i++){
            int left=i>channels?row[i-channels]&255:0,up=previous[i]&255;
            int upperLeft=i>channels?previous[i-channels]&255:0;
            int predictor=filter==1?left:filter==2?up:filter==3?(left+up)/2:paeth(left,up,upperLeft);
            row[i]=(byte)((row[i]&255)+predictor);
        }
    }
    private static void writeRow(byte[] row,byte[] pixels,int offset,int color,int channels,byte[] palette,byte[] transparency)throws IOException{
        int transparentR=-1,transparentG=-1,transparentB=-1;
        if(transparency!=null&&(color==0||color==2)){
            transparentR=u16(transparency,0);
            if(color==2){transparentG=u16(transparency,2);transparentB=u16(transparency,4);}
        }
        for(int i=1;i<row.length;i+=channels){
            int r,g,b,a=255;
            if(color==6||color==2){
                r=row[i]&255;g=row[i+1]&255;b=row[i+2]&255;
                if(color==6)a=row[i+3]&255;
                else if(r==transparentR&&g==transparentG&&b==transparentB)a=0;
            }else if(color==3){
                int index=row[i]&255;
                need(index<palette.length/3,"像素调色板编号越界");
                r=palette[index*3]&255;g=palette[index*3+1]&255;b=palette[index*3+2]&255;
                if(transparency!=null&&index<transparency.length)a=transparency[index]&255;
            }else{
                r=g=b=row[i]&255;
                if(color==4)a=row[i+1]&255;
                else if(r==transparentR)a=0;
            }
            pixels[offset++]=(byte)r;pixels[offset++]=(byte)g;pixels[offset++]=(byte)b;pixels[offset++]=(byte)a;
        }
    }
    public static byte[] encode(byte[] rgba,int width,int height)throws Exception{
        need(width>=1&&height>=1&&width<=MAX_SIDE&&height<=MAX_SIDE&&rgba!=null&&rgba.length==(long)width*height*4,"RGBA尺寸无效");ByteArrayOutputStream compressed=new ByteArrayOutputStream();try(DeflaterOutputStream zipped=new DeflaterOutputStream(compressed)){for(int y=0;y<height;y++){zipped.write(0);zipped.write(rgba,y*width*4,width*4);}}
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);out.write(SIGNATURE);ByteArrayOutputStream header=new ByteArrayOutputStream();DataOutputStream fields=new DataOutputStream(header);fields.writeInt(width);fields.writeInt(height);fields.write(new byte[]{8,6,0,0,0});chunk(out,"IHDR",header.toByteArray());chunk(out,"IDAT",compressed.toByteArray());chunk(out,"IEND",new byte[0]);out.flush();need(bytes.size()<=MAX_PNG,"导出PNG超过32MiB");return bytes.toByteArray();
    }
    private static void chunk(DataOutputStream out,String type,byte[] data)throws Exception{byte[] name=type.getBytes("US-ASCII");out.writeInt(data.length);out.write(name);out.write(data);CRC32 crc=new CRC32();crc.update(name);crc.update(data);out.writeInt((int)crc.getValue());}
}
