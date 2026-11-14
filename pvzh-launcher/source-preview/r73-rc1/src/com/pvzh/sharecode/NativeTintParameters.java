package com.pvzh.sharecode;

import java.math.BigDecimal;
import java.util.Locale;

/** Session-owned values and latest-only preview tickets; views never reset these while drawing. */
public final class NativeTintParameters {
    public static final class Ticket {
        public final String session;public final long version;public final int rgb,strength;
        private Ticket(String session,long version,int rgb,int strength){this.session=session;this.version=version;this.rgb=rgb;this.strength=strength;}
    }
    private String session,previewToken;private int rgb,strength,savedRgb,savedStrength;private long version;private Ticket active;private boolean closed;
    public synchronized void load(String token,int color,int amount){check(color,amount);if(token==null||token.isEmpty())throw new IllegalArgumentException("缺少调色会话");session=token;rgb=savedRgb=color;strength=savedStrength=amount;version++;previewToken=null;active=null;closed=false;}
    private static void check(int color,int amount){if(color<0||color>0xffffff||amount<0||amount>1000)throw new IllegalArgumentException("颜色需为RGB 0～255，强度需0～100%");}
    public synchronized boolean set(int color,int amount){check(color,amount);if(closed||session==null)throw new IllegalStateException("调色会话未打开");if(rgb==color&&strength==amount)return false;rgb=color;strength=amount;version++;previewToken=null;return true;}
    public synchronized boolean channel(int channel,int value){if(channel<0||channel>2||value<0||value>255)throw new IllegalArgumentException("RGB请输入0～255的整数");int shift=(2-channel)*8;return set((rgb&~(255<<shift))|(value<<shift),strength);}
    public synchronized boolean strength(int value){return set(rgb,value);}
    public synchronized boolean preset(int color){return set(color,strength==0?1000:strength);}
    public synchronized boolean resetSaved(){return set(savedRgb,savedStrength);}
    public synchronized boolean dirty(){return session!=null&&!closed&&(rgb!=savedRgb||strength!=savedStrength);}
    public synchronized boolean needsPreview(){return dirty()&&previewToken==null;}
    public synchronized Ticket beginPreview(){return beginPreview(false);}
    public synchronized Ticket beginPreview(boolean refresh){
        if(closed||session==null||active!=null||!refresh&&!needsPreview())return null;
        previewToken=null;
        active=new Ticket(session,version,rgb,strength);
        return active;
    }
    public synchronized boolean current(Ticket value){return value!=null&&!closed&&session!=null&&session.equals(value.session)&&version==value.version&&rgb==value.rgb&&strength==value.strength;}
    public synchronized boolean complete(Ticket value,String token){if(active!=value)return false;active=null;if(!current(value)||token==null||token.isEmpty())return false;previewToken=token;return true;}
    public synchronized boolean fail(Ticket value){if(active!=value)return false;active=null;return current(value);}
    public synchronized void invalidatePreview(){previewToken=null;}
    public synchronized boolean inFlight(){return active!=null;}
    public synchronized boolean canSave(){return dirty()&&active==null&&previewToken!=null;}
    public synchronized Ticket saveTicket(){return canSave()?new Ticket(session,version,rgb,strength):null;}
    public synchronized void close(){closed=true;version++;active=null;previewToken=null;}
    public synchronized String session(){return session;}public synchronized int rgb(){return rgb;}public synchronized int strength(){return strength;}public synchronized int savedRgb(){return savedRgb;}public synchronized int savedStrength(){return savedStrength;}public synchronized long version(){return version;}public synchronized String previewToken(){return previewToken;}
    public synchronized String hex(){return String.format(Locale.ROOT,"#%06X",rgb);}
    public static String percent(int amount){if(amount<0||amount>1000)throw new IllegalArgumentException("强度超出范围");return BigDecimal.valueOf(amount,1).stripTrailingZeros().toPlainString();}
    public static int parsePercent(String value){try{BigDecimal n=new BigDecimal(value.trim());int amount=n.movePointRight(1).intValueExact();if(amount<0||amount>1000)throw new ArithmeticException();return amount;}catch(RuntimeException error){throw new IllegalArgumentException("请输入0～100的百分比，最多一位小数");}}
    public static int parseChannel(String value){if(value==null||!value.trim().matches("[0-9]{1,3}"))throw new IllegalArgumentException("请输入0～255的整数");int n=Integer.parseInt(value.trim());if(n>255)throw new IllegalArgumentException("请输入0～255的整数");return n;}
}
