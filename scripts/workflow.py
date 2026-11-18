#!/usr/bin/env python3
"""Sổ chạy tuần tự + cổng gửi video fail-closed; không cần thư viện ngoài."""
import argparse, hashlib, json, math, os, pathlib, re, shutil, subprocess, sys, tempfile, urllib.request, urllib.parse, uuid
from datetime import datetime, timezone
from importlib.util import spec_from_file_location, module_from_spec
P = pathlib.Path


def _resolve_root() -> P:
    """Thư mục dự án trên máy ĐANG chạy, không giả định máy đóng gói.

    Thứ tự: `HT_PROJECT_ROOT` -> `~/TAN-CONG-TOP-VIEW` -> dò vài chỗ thường
    đặt. Không thấy cái nào thì trả đường mặc định để lệnh báo «thiếu dự án»
    kèm cách chỉ đường, KHÔNG tự tạo thư mục rỗng.
    """
    env = os.environ.get("HT_PROJECT_ROOT", "").strip()
    if env:
        cand = P(env).expanduser()
        if cand.is_dir():
            return cand.resolve()
    default = P.home() / "TAN-CONG-TOP-VIEW"
    if default.is_dir():
        return default.resolve()
    for base in (
        P.cwd(),
        P.home() / "projects",
        P.home() / "code",
        P.home() / "Documents",
        P("/opt"),
        P("/srv"),
        P("/workspace"),
        P("/data"),
    ):
        cand = base / "TAN-CONG-TOP-VIEW"
        if cand.is_dir():
            return cand.resolve()
    return default


ROOT = _resolve_root()
SKILL = P(__file__).resolve().parents[1]
BASE = os.environ.get("HT_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
STAGES = ["lessons","health","interview","plan","assets","scenes","storyboards","approval","video","export","lessons_end","done"]
QUESTIONS = ["theme","title","duration_minutes","language","characters"]
def need(ok, msg):
    if not ok: raise ValueError(msg)
def digest(o):
    return hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def read(p):
    return json.loads(P(p).read_text(encoding="utf-8"))
def save(p,o):
    p=P(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(o,f,ensure_ascii=False,indent=2); f.write("\n")
    os.replace(tmp,p)
def rpc(name,args):
    req=urllib.request.Request(BASE+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":args}}).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: data=json.load(r)
    need(not data.get("error"),"MCP lỗi")
    result=data.get("result") or {}
    need(not result.get("isError") and result.get("content"),"MCP không trả kết quả hợp lệ")
    return json.loads(result["content"][0]["text"])
def health():
    need(
        (ROOT/"backend").is_dir(),
        f"thiếu dự án: không thấy {ROOT}/backend. Đặt HT_PROJECT_ROOT=<thư mục dự án> "
        "rồi chạy lại, hoặc clone repo về đúng ~/TAN-CONG-TOP-VIEW",
    )
    with urllib.request.urlopen(BASE+"/health",timeout=8) as r: need(json.load(r).get("ok") is True,"backend không khỏe")
    with urllib.request.urlopen("http://127.0.0.1:3001/",timeout=8) as r: need(r.status==200,"giao diện không khỏe")
def name(s):
    return re.split(r"\s+[—–-]\s+",str(s),maxsplit=1)[0].strip().casefold()
def plan(folder,s):
    b=read(folder/"brief.json"); m=read(folder/"manifest.json")
    a=s["answers"]
    need(b.get("title")==a["title"] and b.get("idea") and b.get("language")==a["language"],"brief thiếu/sai tên, ý tưởng hoặc ngôn ngữ")
    need(float(b.get("duration_seconds",0))==float(a["duration_minutes"])*60,"brief sai thời lượng")
    need(isinstance(b.get("characters"),list) and isinstance(b.get("scenes"),list) and b["scenes"],"brief thiếu characters/scenes")
    need(b.get("aspect") and b.get("project_id"),"brief thiếu aspect/project_id")
    need((folder/"script.md").is_file() and (folder/"script.md").stat().st_size>0,"thiếu kịch bản script.md")
    assets=m.get("assets"); shots=m.get("shots")
    need(isinstance(assets,list) and isinstance(shots,list),"manifest thiếu assets/shots")
    keys=[name(x["name"]) for x in assets]
    need(len(keys)==len(set(keys)) and all(keys),"tên tài sản trống/trùng")
    need(all(x.get("kind") in {"character","environment","object","style","product","custom"} for x in assets),"loại tài sản sai")
    characters={name(x if isinstance(x,str) else x["name"]) for x in b["characters"]}
    need(characters=={name(x if isinstance(x,str) else x["name"]) for x in json.loads(a["characters"])},"brief không khớp dàn nhân vật đã chốt")
    need(characters <= {name(x["name"]) for x in assets if x["kind"]=="character"},"manifest thiếu nhân vật trong brief")
    expected=[]
    for i,scene in enumerate(b["scenes"],1):
        need(scene.get("title") and scene.get("summary") and scene.get("shots"),f"cảnh {i} thiếu nội dung/cú")
        for j,prompt in enumerate(scene["shots"],1):
            need(isinstance(prompt,str) and prompt.strip(),f"cú {i}.{j} thiếu prompt")
            expected.append(f"{i}.{j}")
    need([x["id"] for x in shots]==expected,"manifest phải đủ mọi cú và đúng thứ tự brief")
    need(len(shots)>=math.ceil(float(b["duration_seconds"])/(124/24)),"chưa đủ số cú cho thời lượng")
    for x in shots:
        refs=x.get("assets")
        need(isinstance(refs,list) and len(refs)==len(set(refs)) and all(name(k) in keys for k in refs),f"cú {x['id']} thiếu/sai danh sách tài sản")
    used={name(k) for x in shots for k in x["assets"]}
    need(characters<=used,"có nhân vật chưa xuất hiện trong cú nào")
    return b,m
def node_details(canvas):
    raw=rpc("canvas_state_get",{"canvas_id":canvas,"fields":["nodes.identity","nodes.generation"]})
    need(raw.get("canvas_id")==canvas and isinstance(raw.get("nodes"),list),"không đọc được đúng canvas")
    ids=[x["node_id"] for x in raw["nodes"] if x["type"] in ("asset","scene")]
    out={}
    for i in range(0,len(ids),50):
        rows=rpc("canvas_node_details",{"canvas_id":canvas,"node_ids":ids[i:i+50]}).get("node_details",[])
        for n in rows: out[n["node_id"]]=n
    need(set(ids)==set(out),"thiếu chi tiết node")
    return out
def media_path(ref):
    need(isinstance(ref,dict) and ref.get("object_key"),"media thiếu object_key")
    root=P(os.environ.get("HT_STORAGE_DIR") or ROOT/"backend/storage").expanduser().resolve()
    p=(root/ref["object_key"]).resolve()
    need(p.is_relative_to(root) and p.is_file() and p.stat().st_size>0,"media không có tệp thật trong kho")
    return p
def probe(p,audio=False):
    exe=shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    out=subprocess.check_output([exe,"-v","error","-show_streams","-show_format","-of","json",str(p)],stderr=subprocess.DEVNULL,timeout=30)
    d=json.loads(out); streams=d.get("streams",[])
    need(any(x.get("codec_type")=="video" and x.get("width",0)>0 for x in streams),"media không có hình đọc được")
    if audio:
        need(any(x.get("codec_type")=="audio" for x in streams),"video thiếu tiếng")
        need(float(d.get("format",{}).get("duration",0))>0,"video thiếu thời lượng")
    return d
def image(n):
    p=n["props"]; ref=p.get("storyboard_media_ref") if n["type"]=="scene" else None
    ref=ref or p.get("media_ref")
    need(isinstance(ref,dict) and ref.get("media_type")=="image",f"thẻ {n['node_id']} thiếu ảnh")
    path=media_path(ref); probe(path)
    return [ref["object_key"],path.stat().st_size,path.stat().st_mtime_ns]
def gate(folder,s,level):
    b,m=plan(folder,s); canvas=m.get("canvas_id")
    need(canvas,"manifest thiếu canvas_id")
    nodes=node_details(canvas); amap={}; stamp={}
    for a in m["assets"]:
        nid=a.get("node_id"); n=nodes.get(nid,{})
        need(n.get("type")=="asset" and n["props"].get("asset_kind")==a["kind"] and name(n["props"].get("title"))==name(a["name"]),f"thiếu/sai thẻ tài sản {a['name']}")
        need(nid not in amap.values(),"hai tài sản dùng cùng node")
        amap[name(a["name"])]=nid; stamp[nid]=image(n)
    actual_assets={k for k,n in nodes.items() if n["type"]=="asset"}
    need(actual_assets==set(amap.values()),"canvas có tài sản ngoài manifest: đối chiếu lại, không bỏ qua")
    if level=="assets": return
    scene_ids=[]
    for i,x in enumerate(m["shots"],1):
        nid=x.get("node_id"); n=nodes.get(nid,{})
        need(n.get("type")=="scene",f"thiếu thẻ cảnh/cú {x['id']}")
        p=n["props"]
        need(nid not in scene_ids and p.get("scene_number")==i and p.get("scene_text"),f"sai/trùng thứ tự hoặc nội dung cú {x['id']}")
        expected={amap[name(k)] for k in x["assets"]}
        need(set(p.get("reference_node_ids") or [])==expected,f"cú {x['id']} sai/thiếu dây ảnh tài sản")
        scene_ids.append(nid)
        if level=="storyboards": stamp[nid]=image(n)
    need({k for k,n in nodes.items() if n["type"]=="scene"}==set(scene_ids),"số thẻ cảnh không khớp toàn bộ manifest")
    if level=="storyboards":
        return digest({"brief":b,"manifest":m,"images":stamp,"script":(folder/"script.md").read_text()})
def stage(s,expected):
    need(s["stage"]==expected,f"CHẶN: đang ở {s['stage']}, không được nhảy tới {expected}")
def move(s,to):
    need(STAGES.index(to)==STAGES.index(s["stage"])+1,"không được bỏ bước")
    s["history"].append({"stage":s["stage"],"at":datetime.now(timezone.utc).isoformat()})
    s["stage"]=to
def authorized(folder,s):
    stage(s,"video"); need(s.get("approval"),"chưa có người dùng đồng ý GPU")
    need(gate(folder,s,"storyboards")==s.get("image_stamp"),"ảnh/brief/bảng vẽ thay đổi: phải kiểm và xin phép lại")
def submit_payload(s,m,shot,p):
    stage(s,"video")
    x=next((x for x in m["shots"] if x["id"]==shot),None); need(x,"cú không tồn tại")
    need(p.get("canvas_id")==m["canvas_id"] and p.get("scene_node_id")==x["node_id"] and p.get("media_type")=="video","payload sai canvas/cú/media")
    need(p.get("prompt") and p.get("capability_version") and p.get("model"),"payload thiếu prompt/capability/model")
    need(p.get("task_type") in ("image_to_video","reference_to_video"),"cấm text_to_video")
    ordered=[x["id"] for x in m["shots"]]
    need(all(k in s.get("clips",{}) for k in ordered[:ordered.index(shot)]),"cú trước chưa có video thật; không nhảy cú")
    inputs=p.get("inputs") or []
    required="start_frame" if p["task_type"]=="image_to_video" else "reference_image"
    scene_input=[v for v in inputs if v.get("role")==required and v.get("source",{}).get("kind")=="canvas_node" and v["source"].get("node_id")==x["node_id"]]
    need(scene_input,"payload không dùng storyboard của chính cú")
    if required=="start_frame": need(sum(v.get("role")==required for v in inputs)==1,"start_frame phải đúng một ảnh")
    allow={x["node_id"]}|{a["node_id"] for a in m["assets"] if name(a["name"]) in {name(k) for k in x["assets"]}}
    need(all(v.get("source",{}).get("kind")=="canvas_node" and v["source"].get("node_id") in allow for v in inputs),"ảnh input không thuộc cú")
    return x
def selftest():
    cases=[]
    def rejected(fn):
        try: fn(); return False
        except ValueError: return True
    s={"stage":"lessons","history":[]}
    cases.append(("nhảy trước phỏng vấn",rejected(lambda:move(s,"plan"))))
    cases.append(("GPU khi chưa tới video",rejected(lambda:stage(s,"video"))))
    m={"canvas_id":"c","assets":[],"shots":[{"id":"1.1","node_id":"n","assets":[]}]}
    s={"stage":"video"}
    p={"canvas_id":"c","scene_node_id":"n","media_type":"video","prompt":"a","capability_version":"v","model":"m","task_type":"text_to_video","inputs":[]}
    cases.append(("cấm chữ -> video",rejected(lambda:submit_payload(s,m,"1.1",p))))
    p["task_type"]="image_to_video"
    cases.append(("cấm thiếu ảnh",rejected(lambda:submit_payload(s,m,"1.1",p))))
    p["inputs"]=[{"role":"start_frame","source":{"kind":"canvas_node","node_id":"wrong"}}]
    cases.append(("cấm sai storyboard",rejected(lambda:submit_payload(s,m,"1.1",p))))
    p["inputs"][0]["source"]["node_id"]="n"
    cases.append(("payload đúng qua",submit_payload(s,m,"1.1",p)["id"]=="1.1"))
    # Kiểm cổng ảnh với fixture, tuyệt đối không gọi API/server/GPU.
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as tmp:
        folder=P(tmp)
        brief={"title":"T","idea":"I","duration_seconds":180,"language":"EN","aspect":"16:9","project_id":"p","characters":["Lena"],"scenes":[{"title":"S","summary":"S","shots":[f"cú {i}" for i in range(35)]}]}
        answers={"theme":"I","title":"T","duration_minutes":"3","language":"EN","characters":'["Lena"]'}
        state={"answers":answers,"stage":"storyboards"}
        manifest={"canvas_id":"c","assets":[{"name":"Lena","kind":"character","node_id":"a"}],"shots":[{"id":f"1.{i}","assets":["Lena"],"node_id":f"s{i}"} for i in range(1,36)]}
        save(folder/"brief.json",brief); save(folder/"manifest.json",manifest); (folder/"script.md").write_text("kịch bản")
        nodes={"a":{"node_id":"a","type":"asset","props":{"title":"Lena","asset_kind":"character","media_ref":{"media_type":"image","object_key":"a.png"}}}}
        for i in range(1,36):
            nodes[f"s{i}"]={"node_id":f"s{i}","type":"scene","props":{"scene_number":i,"scene_text":f"cú {i}","reference_node_ids":["a"],"media_ref":{"media_type":"image","object_key":f"s{i}.png"}}}
        def fake_image(n):
            ref=n["props"].get("media_ref") or {}
            need(ref.get("media_type")=="image" and ref.get("object_key"),"thiếu ảnh")
            return [ref["object_key"],1,1]
        with patch(__name__+".node_details",return_value=nodes),patch(__name__+".image",side_effect=fake_image):
            stamp=gate(folder,state,"storyboards"); cases.append(("đủ 35 cú và đúng dây qua gate",bool(stamp)))
            keep=nodes.pop("s35"); cases.append(("thiếu một thẻ cảnh",rejected(lambda:gate(folder,state,"storyboards")))); nodes["s35"]=keep
            keep=nodes["s1"]["props"].pop("media_ref"); cases.append(("thiếu một storyboard",rejected(lambda:gate(folder,state,"storyboards")))); nodes["s1"]["props"]["media_ref"]=keep
            nodes["s1"]["props"]["reference_node_ids"]=[]; cases.append(("có ảnh nhưng thiếu dây",rejected(lambda:gate(folder,state,"storyboards")))); nodes["s1"]["props"]["reference_node_ids"]=["a"]
            keep=nodes.pop("a"); cases.append(("thiếu nhân vật",rejected(lambda:gate(folder,state,"storyboards")))); nodes["a"]=keep
            state["stage"]="video"; cases.append(("đủ ảnh nhưng chưa đồng ý",rejected(lambda:authorized(folder,state))))
            state["approval"]={"reply":"có"}; state["image_stamp"]=stamp
            nodes["s1"]["props"]["media_ref"]["object_key"]="changed.png"; cases.append(("đổi ảnh sau đồng ý phải chặn",rejected(lambda:authorized(folder,state))))
        cases.append(("tệp ảnh giả không tồn tại",rejected(lambda:media_path({"object_key":"__test_missing__"}))))
        m2={"canvas_id":"c","assets":[],"shots":[{"id":"1.1","node_id":"n","assets":[]},{"id":"1.2","node_id":"n2","assets":[]}]}
        p["scene_node_id"]="n2"; p["inputs"][0]["source"]["node_id"]="n2"
        cases.append(("không nộp cú 2 khi cú 1 chưa xong",rejected(lambda:submit_payload(s,m2,"1.2",p))))
    for label,ok in cases: print(("ĐẠT " if ok else "HỎNG ")+label)
    print(f"{sum(ok for _,ok in cases)}/{len(cases)} tình huống đúng")
    return 0 if all(ok for _,ok in cases) else 1
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["init","status","advance","answer","approve","preflight","submit","refresh","repair","export","finish","rewind","selftest"])
    ap.add_argument("--run"); ap.add_argument("--value"); ap.add_argument("--field"); ap.add_argument("--shot"); ap.add_argument("--payload"); ap.add_argument("--file")
    args=ap.parse_args()
    if args.action=="selftest": return selftest()
    need(args.run,"thiếu --run, dùng cùng mã suốt phim")
    need(re.fullmatch(r"[a-zA-Z0-9_-]{1,80}",args.run),"mã run không hợp lệ")
    need(
        ROOT.is_dir(),
        f"thiếu thư mục dự án {ROOT}: đặt HT_PROJECT_ROOT=<thư mục dự án> rồi chạy lại "
        "(không tự tạo thư mục rỗng)",
    )
    folder=ROOT/".tmp/auto-htgroup"/args.run; path=folder/"state.json"
    if args.action=="init":
        need(not path.exists(),"run đã có; dùng status để tiếp tục")
        save(path,{"stage":"lessons","history":[],"answers":{},"tasks":{},"clips":{}})
        print(folder); return 0
    s=read(path); action=args.action
    if action=="status":
        print(json.dumps(s,ensure_ascii=False,indent=2)); return 0
    if action=="answer":
        stage(s,"interview"); key=QUESTIONS[len(s["answers"])]
        need(args.field==key and args.value and args.value.strip(),"trả lời đúng mục tiếp theo: "+key)
        if key=="duration_minutes": need(float(args.value)>=3 and math.isfinite(float(args.value)),"tối thiểu 3 phút")
        if key=="characters": need(isinstance(json.loads(args.value),list),"characters cần mảng JSON")
        s["answers"][key]=args.value.strip()
        if len(s["answers"])==5: move(s,"plan")
    elif action=="advance":
        st=s["stage"]
        if st=="lessons":
            need((SKILL/"references/BAI-HOC.md").read_text().strip() and args.value,"đọc bài học, ghi xác nhận")
            move(s,"health")
        elif st=="health": health(); move(s,"interview")
        elif st=="plan": plan(folder,s); move(s,"assets")
        elif st in ("assets","scenes"): gate(folder,s,st); move(s,STAGES[STAGES.index(st)+1])
        elif st=="storyboards":
            s["image_stamp"]=gate(folder,s,st); move(s,"approval")
            print("ĐỦ ẢNH — tất cả tài sản, storyboard, dây nối và tệp thật đạt")
        elif st=="video":
            _,m=plan(folder,s)
            need(set(s["clips"])=={x["id"] for x in m["shots"]},"còn cú chưa có video thật")
            for clip in s["clips"].values(): probe(media_path(clip),True)
            move(s,"export")
        elif st=="lessons_end":
            need(args.value and (SKILL/"references/BAI-HOC.md").is_file(),"ghi bài học hoặc xác nhận không có lỗi mới")
            move(s,"done")
        else: raise ValueError("bước hiện tại cần lệnh chuyên biệt, không được advance")
    elif action=="approve":
        stage(s,"approval"); need(args.value in ("có","đồng ý bật GPU"),"chưa có đồng ý GPU rõ ràng")
        need(gate(folder,s,"storyboards")==s["image_stamp"],"bảng/ảnh đổi, kiểm lại")
        s["approval"]={"reply":args.value,"at":datetime.now(timezone.utc).isoformat()}; move(s,"video")
    elif action=="rewind":
        need(not s["tasks"] and not s["clips"] and s["stage"] in ("assets","scenes","storyboards","approval","video"),"đã có task hoặc không ở khâu ảnh; xử lý thủ công không xóa trạng thái")
        s["history"].append({"rewind_from":s["stage"],"reason":args.value or "kiểm lại ảnh"})
        s["stage"]="assets"; s.pop("approval",None); s.pop("image_stamp",None)
    elif action=="preflight": authorized(folder,s); print("ĐƯỢC PHÉP — cổng ảnh + xác nhận GPU hợp lệ")
    elif action=="submit":
        authorized(folder,s); _,m=plan(folder,s); p=read(args.payload)
        x=submit_payload(s,m,args.shot,p)
        need(args.shot not in s["clips"],"cú đã xong")
        old=s["tasks"].get(args.shot)
        need(not old or not old.get("task_id"),"đã có task, dùng refresh")
        # Giữ mã nộp ổn định nếu mạng đứt; không nộp hai lượt.
        p["command_id"]=(old or {}).get("command_id") or str(uuid.uuid4())
        h=digest(p); need(not old or old["hash"]==h,"payload đã đổi trong lần nộp chưa rõ kết quả")
        s["tasks"][args.shot]={"command_id":p["command_id"],"hash":h}; save(path,s)
        r=rpc("generation_submit",p); need(r.get("task_id"),"submit chưa trả task_id; kiểm lại bằng cùng mã")
        s["tasks"][args.shot].update(task_id=r["task_id"],node_id=r.get("node_id")); print("task_id="+r["task_id"])
    elif action=="refresh":
        stage(s,"video"); _,m=plan(folder,s); task=s["tasks"].get(args.shot) or {}
        need(task.get("task_id"),"chưa có task_id")
        p={"canvas_id":m["canvas_id"],"task_id":task["task_id"],"command_id":str(uuid.uuid4())}
        if task.get("node_id"): p["node_id"]=task["node_id"]
        r=rpc("generation_refresh",p); st=r.get("status"); print("generation_status="+str(st))
        if st=="success":
            ref=r.get("media_ref"); need(isinstance(ref,dict) and ref.get("media_type")=="video","success nhưng thiếu video")
            probe(media_path(ref),True)
            s["clips"][args.shot]=ref
        elif st=="fail":
            task["failed"]=True; save(path,s)
            raise ValueError("cú hỏng: dừng, sửa đúng cú, không đánh dấu hoàn tất")
        else: need(st in ("init","queued","running"),"trạng thái lạ")
    elif action=="repair":
        authorized(folder,s); task=s["tasks"].get(args.shot) or {}
        need(task.get("failed") and args.value,"chỉ sửa cú đã xác nhận fail, ghi cách sửa")
        need(not any(t.get("shot")==args.shot for t in s.get("repairs",[])),"đã sửa một lần; dừng báo lỗi")
        s.setdefault("repairs",[]).append({"shot":args.shot,"task":task,"fix":args.value})
        del s["tasks"][args.shot]
    elif action=="export":
        stage(s,"export"); b,m=plan(folder,s)
        t=rpc("timeline_get",{"canvas_id":m["canvas_id"]})
        clips=sorted([x for x in t["draft"]["clips"] if x.get("media_type")=="video"],key=lambda x:x["start_ms"])
        expected=[s["tasks"][x["id"]]["node_id"] for x in m["shots"]]
        need([x.get("source_node_id") for x in clips]==expected,"timeline sai thứ tự hoặc thiếu/thừa cú")
        need(all(x.get("media_ref",{}).get("object_key")==s["clips"][y["id"]]["object_key"] for x,y in zip(clips,m["shots"])),"timeline trỏ nhầm media")
        need(clips and clips[0]["start_ms"]==0 and all(abs(x["start_ms"]+x["duration_ms"]-y["start_ms"])<=2 for x,y in zip(clips,clips[1:])),"timeline có khoảng hở/chồng clip")
        need(t["draft"].get("duration_ms",0)>=float(b["duration_seconds"])*1000,"timeline chưa đủ thời lượng")
        need(not s.get("export_task"),"đã có task xuất, dùng finish")
        s.setdefault("export_command",str(uuid.uuid4())); save(path,s)
        r=rpc("timeline_export",{"canvas_id":m["canvas_id"],"command_id":s["export_command"],"export_type":"full_video","range":{"start_ms":0,"end_ms":round(float(b["duration_seconds"])*1000)}})
        need(r.get("task_id"),"xuất chưa trả task_id")
        s["export_task"]=r["task_id"]; print("export_task="+r["task_id"])
    elif action=="finish":
        stage(s,"export"); _,m=plan(folder,s)
        need(s.get("export_task"),"chưa xuất qua cổng")
        r=rpc("timeline_export_status",{"canvas_id":m["canvas_id"],"task_id":s["export_task"]})
        need(r.get("status")=="success" and r.get("output_url"),"xuất chưa thành công")
        p=P(args.file).expanduser().resolve()
        # API trả output_url=file:// và download_url=/v1/... (nếu có).
        url=urllib.parse.urljoin(BASE,r.get("download_url") or r["output_url"])
        parsed=urllib.parse.urlsplit(url)
        local=None
        if parsed.scheme=="file":
            local=P(urllib.request.url2pathname(parsed.path)).resolve()
            roots=[(ROOT/"backend/storage").resolve()]
            if os.environ.get("HT_EXPORT_DIR"): roots.append(P(os.environ["HT_EXPORT_DIR"]).expanduser().resolve())
            if os.environ.get("HT_STORAGE_DIR"): roots.append(P(os.environ["HT_STORAGE_DIR"]).expanduser().resolve())
            need(parsed.netloc in ("","localhost") and local.suffix.lower()==".mp4" and local.is_file() and any(local.is_relative_to(x) for x in roots),"tệp xuất ngoài kho đã xác minh")
        else:
            need(parsed.scheme=="http" and parsed.netloc==urllib.parse.urlsplit(BASE).netloc,"URL xuất không thuộc backend 8001")
        need(p.is_relative_to((P.home()/"Downloads").resolve()) and p.suffix.lower()==".mp4","đích phải là file mp4 trong Downloads")
        need(p.parent.is_dir(),"thư mục đích chưa tồn tại")
        need(not p.exists(),"tệp đích đã tồn tại; dùng tên mới")
        fd,tmp=tempfile.mkstemp(dir=p.parent,suffix=".mp4")
        try:
            with os.fdopen(fd,"wb") as f:
                with (local.open("rb") if local else urllib.request.urlopen(url,timeout=120)) as rfile: shutil.copyfileobj(rfile,f)
            probe(tmp,True); os.replace(tmp,p)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        need(p.is_relative_to((P.home()/"Downloads").resolve()) and p.is_file() and p.stat().st_size>0,"tệp phim chưa nằm trong Downloads")
        d=probe(p,True); seconds=float(d["format"]["duration"]); b,_=plan(folder,s)
        need(abs(seconds-float(b["duration_seconds"]))<=2,"thời lượng phim lệch quá 2 giây; cắt/sửa rồi đo lại")
        s["delivery"]={"path":str(p),"seconds":seconds,"bytes":p.stat().st_size}; move(s,"lessons_end")
    save(path,s); print("CHECKPOINT="+s["stage"]); return 0
if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        print("CHẶN: "+str(e),file=sys.stderr); sys.exit(1)
