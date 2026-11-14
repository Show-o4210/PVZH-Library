package com.pvzh.sharecode;

import java.io.IOException;

/** Activity-local SAF correlation. An old callback cannot consume a newer target. */
public final class NativeArtworkDocumentRequests {
    private static final int IMPORT_BASE=0x4000,EXPORT_BASE=0x5000,COUNT=0x1000;
    private int imports,exports,importCode=-1,exportCode=-1;private String importToken;private byte[] exportPng;
    public static boolean isImport(int code){return code>=IMPORT_BASE&&code<IMPORT_BASE+COUNT;}
    public static boolean isExport(int code){return code>=EXPORT_BASE&&code<EXPORT_BASE+COUNT;}
    public synchronized int beginImport(String token)throws IOException{if(token==null||token.isEmpty()||token.length()>100)throw new IOException("PNG接收目标无效");if(imports>=COUNT)throw new IOException("本次PNG请求已达上限，请关闭后重新打开启动器");importCode=IMPORT_BASE+imports++;importToken=token;return importCode;}
    public synchronized String takeImport(int code){if(code!=importCode)return null;String token=importToken;importCode=-1;importToken=null;return token;}
    public synchronized void cancelImports(){importCode=-1;importToken=null;}
    public synchronized int beginExport(byte[] png)throws IOException{if(png==null||png.length==0||png.length>NativeArtworkPng.MAX_PNG)throw new IOException("PNG导出快照无效");if(exports>=COUNT)throw new IOException("本次PNG请求已达上限，请关闭后重新打开启动器");exportCode=EXPORT_BASE+exports++;exportPng=png.clone();return exportCode;}
    public synchronized byte[] takeExport(int code){if(code!=exportCode)return null;byte[] value=exportPng;exportPng=null;exportCode=-1;return value;}
    public synchronized void cancelExports(){exportCode=-1;exportPng=null;}
}
