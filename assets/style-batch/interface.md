# 35完整口播：渲染器接口

接受当前口播母片、文稿与时间轴；每个指定画风生成一条完整稿。这里的材料接口适配1080×1920竖屏；其他画幅需要重新构图。原房间坐标与作者人物不作为口播内容。

各JS注册 window.KOUBO_STYLE_FACTORIES[id]=()=>style; shared helper window.KS 提供 rgba/seeded rng/cache/pattern helpers。对象必须含 id,name,palette={paper,ink,red,olive,gold,white}，背景与材料有独特机制，不只调色。

背景加载顺序为 `world_backplate.js` → `egypt_rim_coflow.js` → `shadow_card_occlusion.js` → 主题 scenes。埃及补丁只为02默认埃及配方把实体饰带接入既有相对CAM近层，不改变其他34配方，不增加相机事件。它保留连续背景覆盖断言；长横移中饰带自然离画。自定义埃及rim需重新适配与实片检查。

- background(g,t,shot): 从0,0填满1080×1920，按shot语义画主题布景，禁止原少女猫房间。可用绘画材质/光照/视线/矿物剥落/透视/植物背景等，主要内容由父级主题场景绘制。参数shot={id,start,end,action,object,presenter}。
- pattern(g,col,t): 可选，返回CanvasPattern/CanvasGradient，供主题对象填色，色板对应同一稿的手机、文稿、底片、轨道、磁带、案卷等。pattern应缓存，画面不可每帧整体随机重洗；seed固定。
- plate(g,w,h,col,seed,t): 在当前局部坐标0,0至w,h绘制文稿/声音波形托板/文件夹表面，必须填主面积；可以粗笔/水彩/陶土/岩面/马赛克/金箔/剪纸等；不要额外字。尺寸可能是很小的道具。不能画在字幕区。
- line(g,pts,col,lw,t): 可选，连线/实物轮廓用本风格笔法；waveform点列>100时须轻量，勿逐点长毛笔。保持语义可读。
- motifs(g,t,shot): 可选，绘于背景之后、语义道具/真实照片/标签之前，只在内容区 y<1550 和两侧少量点缀，具体动作按风格且与编辑主题相关；不能喧宾夺主。
- clock(g,x,y,r,hand,t): 可选，返回true表示本风格重画时钟（达利软钟等），含时针分针，不能代码造脸。
- rim(g,t,shot): 可选，真实矢量装饰边层，供连续overscan背景使用；禁止把不透明背景矩形切条贴回。
- after(g,t,shot): 可选，在字幕之前执行，画面材质/光照；不要遮字幕/说明标签。会影响真实人物的光效须温和，保留脸。
- metadata:{mechanism,topic_adaptation,motifs,limitations} 用中文，准确说明实际实现与来源。

KS 接口由root提供：rng(seed)->fn，mix(a,b,q), shade(col,delta), alpha(col,a), cached(key,w,h,fn)->canvas, pattern(g,key,w,h,fn)->pattern, path(g,pts,closed=true), grain(g,w,h,count,seed,alpha), hatch(g,w,h,col,spacing=20,angle=-.6,lw=2), seeded points。PAINT及brush/CL/KIT/MD/CAM原库可直接用，U已setStage1080×1920。缓存key含style id。background阶段不套pattern，plate/line自身用原canvas颜色，不要递归调用pattern。

字幕与未对口型标签由root用固定黑白高对比绘制。真实图库人物频繁回归，保持真实照片，不代码造新人物。风格改变道具形制/材料/背景与母题动作；主题事件共享以便公平比较，但每一版应一眼区分笔法和布景。将具体风格代码写到各自分组文件，不改shared engine，先创建完整代码，再自查。

皮影文字修复仅对V4 notes(seed43)成立：中心source-over实体浅皮纸继承当前alpha，原镂孔边缘仍透光。新主题须主动标记语义卡并复验文字几何，不能假定任意seed或卡片都会自动修复。
