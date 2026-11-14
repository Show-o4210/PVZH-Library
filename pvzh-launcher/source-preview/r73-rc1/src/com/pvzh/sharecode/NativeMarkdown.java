package com.pvzh.sharecode;

import java.net.URI;
import java.util.*;
import java.util.regex.*;

/** Small, non-executing Markdown presentation parser. Source is never rewritten in storage. */
final class NativeMarkdown {
    static final class Mark {
        final String kind,value;final int start,end;
        Mark(String k,int s,int e,String v){kind=k;start=s;end=e;value=v;}
    }
    static final class Document {
        final String text;final List<Mark> marks;
        Document(String s,List<Mark> m){text=s;marks=Collections.unmodifiableList(m);}
    }
    private static final Pattern FENCE=Pattern.compile("^ {0,3}(`{3,}|~{3,})(.*)$");
    private static final Pattern HEADING=Pattern.compile("^ {0,3}(#{1,6})[ \\t]+(.*)$");
    private static final Pattern LIST=Pattern.compile("^( *)([-+*]|[0-9]{1,9}[.)])[ \\t]+(.*)$");
    private final StringBuilder text=new StringBuilder();private final List<Mark> marks=new ArrayList<>();private long remaining;
    static Document parse(String raw){return new NativeMarkdown().blocks(raw==null?"":raw);}
    private void mark(String kind,int start,String value){if(text.length()>start)marks.add(new Mark(kind,start,text.length(),value));}
    private Document blocks(String raw){
        remaining=Math.max(4096L,raw.length()*32L);
        String[] lines=raw.replace("\r\n","\n").replace('\r','\n').split("\n",-1);
        for(int i=0;i<lines.length;i++){
            String line=lines[i];Matcher fence=FENCE.matcher(line);
            if(fence.matches()){
                if(text.length()>0&&text.charAt(text.length()-1)!='\n')text.append('\n');
                char delimiter=fence.group(1).charAt(0);int length=fence.group(1).length(),start=text.length();String language=fence.group(2).trim();
                for(i++;i<lines.length;i++){String close=lines[i].trim();if(close.length()>=length&&all(close,delimiter))break;text.append(lines[i]);if(i+1<lines.length)text.append('\n');}
                mark("code_block",start,language);if(i<lines.length&&i+1<lines.length&&text.length()>0&&text.charAt(text.length()-1)!='\n')text.append('\n');continue;
            }
            int quote=0;String body=line;
            while(body.startsWith(">")){quote++;body=body.substring(1);if(body.startsWith(" "))body=body.substring(1);}
            int start=text.length();Matcher heading=HEADING.matcher(body),list=LIST.matcher(body);
            if(heading.matches()){inline(heading.group(2).replaceFirst("[ \\t]+#+[ \\t]*$",""),0);mark("heading",start,String.valueOf(heading.group(1).length()));}
            else if(list.matches()){
                int indent=list.group(1).length();for(int j=0;j<Math.min(12,indent);j++)text.append(' ');
                String bullet=list.group(2);text.append(bullet.length()==1?"• ":bullet+" ");inline(list.group(3),0);mark("list",start,String.valueOf(indent));
            }else inline(body,0);
            if(quote>0)mark("quote",start,String.valueOf(quote));
            if(i+1<lines.length)text.append('\n');
        }
        return new Document(text.toString(),new ArrayList<>(marks));
    }
    private static boolean all(String s,char c){for(int i=0;i<s.length();i++)if(s.charAt(i)!=c)return false;return true;}
    private static boolean punctuation(char c){return "\\`*_{}[]()#+-.!>~|".indexOf(c)>=0;}
    private void inline(String s,int depth){
        if(depth>=16){text.append(s);return;}
        for(int i=0;i<s.length();){
            if(--remaining<0){text.append(s.substring(i));return;}
            char c=s.charAt(i);
            if(c=='\\'&&i+1<s.length()&&punctuation(s.charAt(i+1))){text.append(s.charAt(i+1));i+=2;continue;}
            if(c=='`'){
                int n=run(s,i,c),end=closingCode(s,i+n,n);
                if(end>=0){int start=text.length();String code=s.substring(i+n,end).replace('\n',' ');if(code.length()>1&&code.startsWith(" ")&&code.endsWith(" ")&&!code.trim().isEmpty())code=code.substring(1,code.length()-1);text.append(code);mark("code",start,"");i=end+n;continue;}text.append(s,i,i+n);i+=n;continue;
            }
            if(c=='['&&(i==0||s.charAt(i-1)!='!')){
                int close=bracket(s,i,'[',']');
                if(close>i&&close+1<s.length()&&s.charAt(close+1)=='('){int end=bracket(s,close+1,'(',')');if(end>close){String url=s.substring(close+2,end).trim();if(url.startsWith("<")&&url.endsWith(">"))url=url.substring(1,url.length()-1);if(safeLink(url)){int start=text.length();inline(s.substring(i+1,close),depth+1);mark("link",start,url);i=end+1;continue;}else{text.append(s,i,end+1);i=end+1;continue;}}}
            }
            if(c=='<'){
                int end=s.indexOf('>',i+1);if(end>i&&safeLink(s.substring(i+1,end))){String url=s.substring(i+1,end);int start=text.length();text.append(url);mark("link",start,url);i=end+1;continue;}
            }
            if((c=='*'||c=='_')&&i+1<s.length()&&!Character.isWhitespace(s.charAt(i+1))&&(c!='_'||i==0||!Character.isLetterOrDigit(s.charAt(i-1)))){
                int n=Math.min(3,run(s,i,c));int end=closingEmphasis(s,i+n,c,n);
                if(end>i+n){int start=text.length();inline(s.substring(i+n,end),depth+1);if(n>=2)mark("bold",start,"");if(n==1||n==3)mark("italic",start,"");i=end+n;continue;}
            }
            text.append(c);i++;
        }
    }
    private static int run(String s,int i,char c){int j=i;while(j<s.length()&&s.charAt(j)==c)j++;return j-i;}
    private int closingCode(String s,int from,int count){for(int i=from;i<s.length();i++){if(--remaining<0)return -1;if(s.charAt(i)=='`'){int n=run(s,i,'`');if(n==count)return i;i+=n-1;}}return -1;}
    private int closingEmphasis(String s,int from,char c,int count){
        for(int i=from;i<s.length();i++){
            if(--remaining<0)return -1;
            if(s.charAt(i)=='\\'){i++;continue;}
            if(s.charAt(i)=='`'){int n=run(s,i,'`'),end=closingCode(s,i+n,n);if(end>=0){i=end+n-1;continue;}}
            if(s.charAt(i)==c){int n=run(s,i,c);if((n==count||n==3)&&i>from&&!Character.isWhitespace(s.charAt(i-1))&&(c!='_'||i+n==s.length()||!Character.isLetterOrDigit(s.charAt(i+n))))return i+n-count;i+=n-1;}
        }return -1;
    }
    private int bracket(String s,int start,char open,char close){int depth=0;for(int i=start;i<s.length();i++){if(--remaining<0)return -1;char c=s.charAt(i);if(c=='\\'){i++;continue;}if(c==open)depth++;else if(c==close&&--depth==0)return i;}return -1;}
    static boolean safeLink(String value){
        if(value==null||value.isEmpty())return false;for(int i=0;i<value.length();i++)if(Character.isISOControl(value.charAt(i))||Character.isWhitespace(value.charAt(i)))return false;
        try{URI uri=new URI(value);String scheme=uri.getScheme();if("https".equalsIgnoreCase(scheme)||"http".equalsIgnoreCase(scheme))return uri.getHost()!=null&&!uri.getHost().isEmpty();return "mailto".equalsIgnoreCase(scheme)&&!uri.getSchemeSpecificPart().isEmpty();}catch(Exception ignored){return false;}
    }
    private NativeMarkdown(){}
}
