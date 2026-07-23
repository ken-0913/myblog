---
title: "LFCS 자격 준비 (6) Users and Groups 실전 문제 + 연습 터미널"
date: 2026-07-22T13:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-06-users-and-groups-f848dd4f.png
---

LFCS 시리즈 마지막 편으로 **Users and Groups (10%)** 도메인을 다룬다.
환경 변수, 사용자·그룹·sudo, 리소스 한도(limits)가 핵심 주제이다.
정리 후 **인터랙티브 연습 터미널**에서 명령을 직접 입력해 본다.

## 1. 환경 변수

`export` 없이 정의한 변수는 현재 셸에만, `export`한 변수는 자식 프로세스에도 전달된다.
`.bashrc` 등 프로필 파일로 로그인 시 자동 설정할 수 있다.

- **값 확인**: `echo $VARIABLE1`, `env | grep VARIABLE`
- **자식까지 전달**: `export VARIABLE3="${VARIABLE1}-extended"`

## 2. 사용자·그룹·sudo

`usermod`로 홈 디렉터리(`-d`)와 기본 그룹(`-g`)을 바꾼다.
`useradd`로 셸(`-s`)·홈(`-d -m`)·보조 그룹(`-G`)을 지정해 만든다.
sudo 권한은 `visudo`로 안전하게 편집한다.

- **홈/그룹 변경**: `usermod -d /home/accounts/user1 user1`, `usermod -g dev user1`
- **사용자 추가**: `useradd -s /bin/bash -m -d /home/accounts/user2 -G dev,op user2`
- **NOPASSWD sudo**: `visudo` → `user2 ALL=(root) NOPASSWD: /bin/bash /root/dangerous.sh`

## 3. 리소스 한도 (limits)

셸의 한도는 `ulimit`로 보고, 영구 설정은 `/etc/security/limits.conf`에 둔다.
`soft`는 사용자가 올릴 수 있고, `hard`는 상한이다.

- **현재 한도**: `ulimit -a`, `ulimit -u`(프로세스 수)
- **영구 설정**: `/etc/security/limits.conf` → `jackie hard nproc 1024`
- **동시 로그인 제한**: `@operators hard maxlogins 1`

```terminal
$ cat /etc/security/limits.conf
jackie      hard    nproc       1024
@operators  hard    maxlogins   1
```

## 연습 터미널 — Users and Groups

문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help` 사용법, `hint` 힌트, `skip` 건너뛰기, `clear` 화면 지우기를 쓸 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Users and Groups</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

<style>
.lfx-term{max-width:760px;margin:1.5rem auto;border-radius:10px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.35);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;background:#0d1117;border:1px solid #30363d}
.lfx-bar{display:flex;align-items:center;gap:.5rem;padding:.55rem .8rem;background:#161b22;border-bottom:1px solid #30363d}
.lfx-dot{width:12px;height:12px;border-radius:50%;display:inline-block}
.lfx-red{background:#ff5f56}.lfx-yellow{background:#ffbd2e}.lfx-green{background:#27c93f}
.lfx-title{margin-left:.5rem;color:#8b949e;font-size:.8rem}
.lfx-body{padding:1rem;height:440px;overflow-y:auto;color:#c9d1d9;font-size:.9rem;line-height:1.55;cursor:text}
.lfx-output{white-space:pre-wrap;word-break:break-word}
.lfx-output .lfx-cmd-echo{color:#c9d1d9}
.lfx-output .lfx-prompt{color:#27c93f;margin-right:.4rem}
.lfx-q{color:#58a6ff}
.lfx-ok{color:#3fb950}
.lfx-err{color:#f0883e}
.lfx-hint{color:#d29922}
.lfx-key{color:#27c93f}
.lfx-block{margin:.25rem 0 .75rem}
.lfx-line{display:flex;align-items:center}
.lfx-prompt{color:#27c93f;margin-right:.4rem;white-space:nowrap}
.lfx-input{flex:1;background:transparent;border:none;outline:none;color:#c9d1d9;font-family:inherit;font-size:.9rem;caret-color:#27c93f}
</style>

<script>
(function(){
  var PROBLEMS = [
    { q:"환경 변수 VARIABLE1 의 값을 출력하라.",
      accept:["echo $VARIABLE1","echo \"$VARIABLE1\""],
      out:"random-string",
      hint:"echo $VARIABLE1." },
    { q:"이름에 VARIABLE 이 들어간 환경 변수를 모두 확인하라.",
      accept:["env | grep VARIABLE","printenv | grep VARIABLE"],
      out:"VARIABLE1=random-string",
      hint:"env | grep VARIABLE." },
    { q:"자식 프로세스에도 전달되도록 VARIABLE3 를 값 ${VARIABLE1}-extended 로 export 하라.",
      accept:["export VARIABLE3=\"${VARIABLE1}-extended\"","export VARIABLE3=${VARIABLE1}-extended"],
      out:"# VARIABLE3 export 됨 (자식 프로세스에서도 사용 가능)",
      hint:"export VARIABLE3=\"${VARIABLE1}-extended\"." },
    { q:"user1 의 홈 디렉터리를 /home/accounts/user1 로 변경하라.",
      accept:["usermod -d /home/accounts/user1 user1","sudo usermod -d /home/accounts/user1 user1"],
      out:"# user1 홈 디렉터리 변경됨",
      hint:"usermod -d <homedir> <user>." },
    { q:"user1 의 기본 그룹(primary group)을 dev 로 변경하라.",
      accept:["usermod -g dev user1","sudo usermod -g dev user1"],
      out:"# user1 기본 그룹 → dev",
      hint:"usermod -g <group> <user>." },
    { q:"user1 이 속한 그룹을 확인하라.",
      accept:["groups user1","id user1"],
      out:"user1 : dev",
      hint:"groups <user> 또는 id <user>." },
    { q:"셸 /bin/bash, 홈 /home/accounts/user2(생성 포함), 보조 그룹 dev,op 로 새 사용자 user2 를 추가하라.",
      accept:["useradd -s /bin/bash -m -d /home/accounts/user2 -G dev,op user2","sudo useradd -s /bin/bash -m -d /home/accounts/user2 -G dev,op user2"],
      out:"# user2 생성됨 (shell /bin/bash, groups dev,op)",
      hint:"useradd -s /bin/bash -m -d /home/accounts/user2 -G dev,op user2." },
    { q:"user2 의 그룹 소속을 /etc/group 에서 확인하라.",
      accept:["cat /etc/group | grep user2","grep user2 /etc/group"],
      out:"op:x:1003:user2\ndev:x:1004:user2\nuser2:x:1005:",
      hint:"grep user2 /etc/group." },
    { q:"sudoers 파일을 안전하게(문법 검증) 편집하는 명령을 실행하라.",
      accept:["visudo","sudo visudo"],
      out:"# visudo: 문법 검증 후 저장됨",
      hint:"항상 visudo 로 편집한다(직접 편집 금지)." },
    { q:"현재 셸의 모든 리소스 한도를 확인하라.",
      accept:["ulimit -a"],
      out:"open files                (-n) 1024\nmax user processes        (-u) 1024\nstack size         (kbytes, -s) 8192",
      hint:"ulimit -a." },
    { q:"최대 사용자 프로세스 수 한도를 확인하라.",
      accept:["ulimit -u"],
      out:"1024",
      hint:"ulimit -u." },
    { q:"사용자·그룹의 리소스 한도를 영구 설정하는 파일의 내용을 확인하라.",
      accept:["cat /etc/security/limits.conf","less /etc/security/limits.conf"],
      out:"jackie      hard    nproc       1024\n@operators  hard    maxlogins   1",
      hint:"영구 한도는 /etc/security/limits.conf 에 설정한다." }
  ];

  var body = document.getElementById("lfx-body");
  var output = document.getElementById("lfx-output");
  var input = document.getElementById("lfx-input");
  if(!body || !output || !input){ return; }

  var idx = 0, solved = 0, history = [], hIndex = -1;

  function scrollDown(){ body.scrollTop = body.scrollHeight; }
  function printBlock(html, cls){
    var div = document.createElement("div");
    div.className = "lfx-block" + (cls ? " " + cls : "");
    div.innerHTML = html;
    output.appendChild(div);
  }
  function echoCommand(raw){
    var div = document.createElement("div");
    div.innerHTML = '<span class="lfx-prompt">lfcs@exam:~$</span><span class="lfx-cmd-echo"></span>';
    div.querySelector(".lfx-cmd-echo").textContent = raw;
    output.appendChild(div);
  }
  function normalize(s){ return s.trim().replace(/\s+/g, " "); }
  function showProblem(){
    if(idx >= PROBLEMS.length){
      printBlock('<span class="lfx-ok">✔ 모든 문제를 마쳤다. 정답 ' + solved + '/' + PROBLEMS.length + '</span>\n다시 풀려면 <span class="lfx-key">reset</span> 을 입력하라.');
      return;
    }
    printBlock('<span class="lfx-q">[문제 ' + (idx+1) + '/' + PROBLEMS.length + '] ' + PROBLEMS[idx].q + '</span>');
  }
  function run(raw){
    var cmd = normalize(raw);
    echoCommand(raw);
    if(cmd !== ""){ history.push(cmd); hIndex = history.length; }
    if(cmd === "clear"){ output.innerHTML = ""; showProblem(); return; }
    if(cmd === "help"){ printBlock("연습 방법:\n  문제를 읽고 알맞은 명령을 입력한다.\n  <span class=\"lfx-key\">hint</span>  힌트    <span class=\"lfx-key\">skip</span>  건너뛰기    <span class=\"lfx-key\">clear</span> 화면지우기    <span class=\"lfx-key\">reset</span> 처음부터"); return; }
    if(cmd === "reset"){ idx = 0; solved = 0; output.innerHTML = ""; printBlock('처음부터 다시 시작한다.'); showProblem(); return; }
    if(idx >= PROBLEMS.length){ printBlock('이미 모든 문제를 마쳤다. <span class="lfx-key">reset</span> 을 입력하라.'); return; }
    var p = PROBLEMS[idx];
    if(cmd === "hint"){ printBlock('<span class="lfx-hint">힌트: ' + p.hint + '</span>'); return; }
    if(cmd === "skip"){ printBlock('<span class="lfx-err">건너뛴다. 정답 예시: ' + p.accept[0] + '</span>'); idx++; showProblem(); return; }
    if(cmd === ""){ return; }
    var ok = p.accept.some(function(a){ return normalize(a) === cmd; });
    if(ok){
      printBlock(p.out);
      printBlock('<span class="lfx-ok">✔ 정답!</span>');
      solved++; idx++; showProblem();
    } else {
      printBlock('<span class="lfx-err">✘ 예상한 명령이 아니다.</span> <span class="lfx-key">hint</span> 로 힌트를, <span class="lfx-key">skip</span> 으로 정답을 볼 수 있다.');
    }
  }

  printBlock('Users and Groups 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
  showProblem();

  input.addEventListener("keydown", function(e){
    if(e.key === "Enter"){ e.preventDefault(); run(input.value); input.value = ""; scrollDown(); }
    else if(e.key === "ArrowUp"){ e.preventDefault(); if(history.length===0){return;} hIndex = Math.max(0, hIndex-1); input.value = history[hIndex] || ""; }
    else if(e.key === "ArrowDown"){ e.preventDefault(); if(history.length===0){return;} hIndex = Math.min(history.length, hIndex+1); input.value = history[hIndex] || ""; }
  });
  body.addEventListener("click", function(){ input.focus(); });
})();
</script>

## 정리

Users and Groups는 비중은 작지만 `usermod`·`useradd`·`visudo`·`ulimit` 같은 필수 명령을 다룬다.
환경 변수의 `export` 여부와 limits의 `soft`/`hard` 차이를 정확히 아는 것이 포인트이다.
이로써 LFCS 5개 도메인 실전 문제 시리즈를 마친다.
