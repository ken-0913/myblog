---
title: "Terminal"
date: 2026-07-16T15:00:00+09:00
---

<div id="ft-terminal" class="ft-terminal"><div class="ft-bar"><span class="ft-dot ft-red"></span><span class="ft-dot ft-yellow"></span><span class="ft-dot ft-green"></span><span class="ft-title">ken@blog: ~</span></div><div id="ft-body" class="ft-body"><div id="ft-output" class="ft-output"></div><div class="ft-line"><span class="ft-prompt">ken@blog:~$</span><input id="ft-input" class="ft-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

<style>
.ft-terminal{max-width:760px;margin:1.5rem auto;border-radius:10px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.35);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;background:#0d1117;border:1px solid #30363d}
.ft-bar{display:flex;align-items:center;gap:.5rem;padding:.55rem .8rem;background:#161b22;border-bottom:1px solid #30363d}
.ft-dot{width:12px;height:12px;border-radius:50%;display:inline-block}
.ft-red{background:#ff5f56}.ft-yellow{background:#ffbd2e}.ft-green{background:#27c93f}
.ft-title{margin-left:.5rem;color:#8b949e;font-size:.8rem}
.ft-body{padding:1rem;height:420px;overflow-y:auto;color:#c9d1d9;font-size:.9rem;line-height:1.55;cursor:text}
.ft-output{white-space:pre-wrap;word-break:break-word}
.ft-output .ft-cmd-echo{color:#c9d1d9}
.ft-output .ft-prompt{color:#27c93f;margin-right:.4rem}
.ft-output a{color:#58a6ff;text-decoration:none}
.ft-output a:hover{text-decoration:underline}
.ft-output .ft-accent{color:#f0883e}
.ft-output .ft-key{color:#27c93f}
.ft-output .ft-err{color:#ff7b72}
.ft-block{margin:.25rem 0 .75rem}
.ft-line{display:flex;align-items:center}
.ft-prompt{color:#27c93f;margin-right:.4rem;white-space:nowrap}
.ft-input{flex:1;background:transparent;border:none;outline:none;color:#c9d1d9;font-family:inherit;font-size:.9rem;caret-color:#27c93f}
</style>

<script>
(function(){
  // ==============================
  //  명령어 정의 — 이 객체만 수정하면 됩니다.
  //  값이 문자열이면 그대로 출력(HTML 허용), 함수면 반환값을 출력.
  // ==============================
  var COMMANDS = {
    help: function(){
      var names = Object.keys(COMMANDS).concat(["clear"]).sort();
      return "사용 가능한 명령어:\n  " + names.map(function(n){return '<span class="ft-key">'+n+'</span>';}).join("  ") +
             "\n\n명령어를 입력하고 Enter를 누르세요. (↑/↓: 히스토리)";
    },
    about: "안녕하세요, <span class=\"ft-accent\">ken</span> 입니다.\n클라우드 네이티브 인프라에 관심이 많은 엔지니어이며,\n주로 Kubernetes, Network, Golang을 다룹니다.\n학습하고 경험한 내용을 이 블로그에 정리합니다.",
    whoami: "ken  (HYEONJAE LEE / 李 賢在 / 이현재)",
    skills: "- <span class=\"ft-accent\">Kubernetes</span> : 클러스터 운영, Service Mesh(Istio)\n- <span class=\"ft-accent\">Network</span>     : 클라우드 네트워크, 트래픽 관리\n- <span class=\"ft-accent\">Golang</span>      : 백엔드 / 도구 개발",
    certs: "🎖  <span class=\"ft-accent\">Kubestronaut</span> (CNCF)\n    CNCF / Kubernetes 관련 자격증 보유\n    자세한 뱃지는 About 페이지에서 확인하세요 → <a href=\"../about/\">/about</a>",
    posts: "최근 글:\n  - <a href=\"../posts/istio-ica-01-prerequisites/\">ICA 시험 정리 (1) 서비스 메시 기초</a>\n  - <a href=\"../posts/istio-ica-03-traffic-management/\">ICA 시험 정리 (3) Traffic Management</a>\n  - <a href=\"../posts/datadog-mcp-server-setup-guide/\">Datadog MCP Server 설정 가이드</a>\n\n전체 목록 → <a href=\"../posts/\">/posts</a>",
    social: "GitHub    : <a href=\"https://github.com/ken-0913\" target=\"_blank\" rel=\"noopener noreferrer\">github.com/ken-0913</a>\nLinkedIn  : <a href=\"https://www.linkedin.com/in/hyeonjae-lee-ab3341175/\" target=\"_blank\" rel=\"noopener noreferrer\">linkedin.com/in/hyeonjae-lee</a>\nEmail     : <a href=\"mailto:hyeonjae0913@gmail.com\">hyeonjae0913@gmail.com</a>",
    contact: function(){ return COMMANDS.social; },
    date: function(){ return new Date().toString(); },
    echo: function(args){ return args.join(" "); }
  };

  var WELCOME = 'Welcome to <span class="ft-accent">ken\'s blog</span> terminal.\n' +
                "'<span class=\"ft-key\">help</span>' 를 입력하면 사용 가능한 명령어를 볼 수 있습니다.";

  var body = document.getElementById("ft-body");
  var output = document.getElementById("ft-output");
  var input = document.getElementById("ft-input");
  if(!body || !output || !input){ return; }

  var history = [];
  var hIndex = -1;

  function scrollDown(){ body.scrollTop = body.scrollHeight; }

  function printBlock(html){
    var div = document.createElement("div");
    div.className = "ft-block";
    div.innerHTML = html;
    output.appendChild(div);
  }

  function echoCommand(raw){
    var div = document.createElement("div");
    div.innerHTML = '<span class="ft-prompt">ken@blog:~$</span><span class="ft-cmd-echo"></span>';
    div.querySelector(".ft-cmd-echo").textContent = raw;
    output.appendChild(div);
  }

  function run(raw){
    var trimmed = raw.trim();
    if(trimmed === ""){ echoCommand(raw); return; }
    echoCommand(raw);
    history.push(trimmed); hIndex = history.length;

    var parts = trimmed.split(/\s+/);
    var name = parts[0].toLowerCase();
    var args = parts.slice(1);

    if(name === "clear"){ output.innerHTML = ""; return; }

    var cmd = COMMANDS[name];
    if(cmd === undefined){
      printBlock('<span class="ft-err">command not found: ' + name + "</span>\n'<span class=\"ft-key\">help</span>' 를 입력해 보세요.");
      return;
    }
    var result = (typeof cmd === "function") ? cmd(args) : cmd;
    printBlock(result);
  }

  // 초기 환영 메시지
  printBlock(WELCOME);

  input.addEventListener("keydown", function(e){
    if(e.key === "Enter"){
      e.preventDefault();
      run(input.value);
      input.value = "";
      scrollDown();
    } else if(e.key === "ArrowUp"){
      e.preventDefault();
      if(history.length === 0){ return; }
      hIndex = Math.max(0, hIndex - 1);
      input.value = history[hIndex] || "";
    } else if(e.key === "ArrowDown"){
      e.preventDefault();
      if(history.length === 0){ return; }
      hIndex = Math.min(history.length, hIndex + 1);
      input.value = history[hIndex] || "";
    }
  });

  // 터미널 아무 곳이나 클릭하면 입력창에 포커스
  body.addEventListener("click", function(){ input.focus(); });
})();
</script>
