---
title: "LFCS 자격 준비 (5) Essential Commands 실전 문제 + 연습 터미널"
date: 2026-07-22T12:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "Git", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-05-essential-commands-8d8aa420.png
---

LFCS 시리즈 다섯 번째 편으로 **Essential Commands (20%)** 도메인을 다룬다.
아카이브·압축, `find`, Git, 출력 리다이렉션, 정규식이 핵심 주제이다.
정리 후 **인터랙티브 연습 터미널**에서 명령을 직접 입력해 본다.

## 1. 아카이브·압축

tar 아카이브는 압축 계층(bzip2·gzip 등)을 바꿀 수 있다.
`bunzip2 -k`로 원본을 유지한 채 해제하고, `gzip --best`로 최고 압축한다.

- **bzip2 해제(원본 유지)**: `bunzip2 -k import001.tar.bz2`
- **gzip 최고 압축**: `gzip --best import001.tar`
- **목록 정렬 출력**: `tar tf import001.tar.gz | sort`

## 2. find로 찾고 실행

`find`는 조건으로 파일을 찾고 `-exec`로 명령을 실행한다.
크기는 `-size`, 권한은 `-perm`, 날짜는 `-newermt`로 비교한다.

- **날짜 이전**: `find ! -newermt "01/01/2020" -type f`
- **크기**: `find -size -3k`(미만), `find -size +10k`(초과)
- **권한**: `find -perm 777`
- **실행/이동**: `-exec rm {} \;`, `-exec mv {} ./small \;`

## 3. Git 기본

로컬 저장소도 `git clone`으로 복제할 수 있다.
브랜치는 `git branch -a`로 보고, `git merge`로 병합하며, `git commit -m`으로 커밋한다.

- **복제**: `git clone /repositories/auto-verifier ~/repositories/auto-verifier`
- **브랜치 목록**: `git branch -a`
- **병합·커밋**: `git merge dev5`, `git commit -m "added log directory"`

## 4. 출력 리다이렉션

stdout은 `1`, stderr는 `2`이다.
`>`는 stdout, `2>`는 stderr, `&>` 또는 `> file 2>&1`은 둘 다 리다이렉트한다.

- **stdout**: `cmd > out.txt`
- **stderr**: `cmd 2> err.txt`
- **둘 다**: `cmd &> all.txt` 또는 `cmd > all.txt 2>&1`
- **종료 코드**: `echo $?`

## 5. 정규식 (grep·sed)

`grep -E`로 확장 정규식 검색, `sed -i 's/A/B/g'`로 치환한다.
`^`는 줄 시작, `$`는 줄 끝, `.*`는 임의 문자열이다.

```terminal
$ grep -E "/app/user.*hacker-bot/1.2" nginx.log
$ sed -i 's/^container.web.*Running.*24h$/SENSITIVE LINE REMOVED/g' server.log
```

## 연습 터미널 — Essential Commands

문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help` 사용법, `hint` 힌트, `skip` 건너뛰기, `clear` 화면 지우기를 쓸 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Essential Commands</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

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
    { q:"원본을 유지하면서 import001.tar.bz2 의 bzip2 압축을 해제하라.",
      accept:["bunzip2 -k import001.tar.bz2","bzip2 -dk import001.tar.bz2"],
      out:"# import001.tar 생성 (원본 .bz2 유지)",
      hint:"bunzip2 -k (원본 유지) 또는 bzip2 -dk." },
    { q:"import001.tar 를 최고 압축률의 gzip 으로 압축하라.",
      accept:["gzip --best import001.tar","gzip -9 import001.tar"],
      out:"# import001.tar.gz 생성 (최고 압축)",
      hint:"gzip --best 또는 gzip -9." },
    { q:"gzip tar 아카이브의 내용 목록을 정렬해 출력하라.",
      accept:["tar tf import001.tar.gz | sort"],
      out:"import001/2ba047d9-...\nimport001/5d517b37-...\nimport001/8b718f8f",
      hint:"tar tf <archive> 로 목록을 뽑아 sort." },
    { q:"2020-01-01 이전에 수정된 일반 파일을 모두 찾아라.",
      accept:["find ! -newermt \"01/01/2020\" -type f","find ! -newermt '01/01/2020' -type f"],
      out:"./backup-0007\n./backup-0142\n... (21개)",
      hint:"find ! -newermt \"01/01/2020\" -type f (해당 날짜보다 오래된 파일)." },
    { q:"크기가 3KiB 미만인 일반 파일을 찾아라.",
      accept:["find -size -3k -type f","find . -size -3k -type f","find -maxdepth 1 -size -3k -type f"],
      out:"./backup-0031\n./backup-0088\n... (24개)",
      hint:"find -size -3k (미만은 -, 초과는 +)." },
    { q:"크기가 10KiB 초과인 일반 파일을 찾아라.",
      accept:["find -size +10k -type f","find . -size +10k -type f","find -maxdepth 1 -size +10k -type f"],
      out:"./backup-0003\n./backup-0210\n... (11개)",
      hint:"find -size +10k." },
    { q:"권한이 정확히 777 인 일반 파일을 찾아라.",
      accept:["find -perm 777 -type f","find . -perm 777 -type f","find -maxdepth 1 -perm 777 -type f"],
      out:"./backup-0055\n./backup-0199\n... (12개)",
      hint:"find -perm 777." },
    { q:"로컬 저장소 /repositories/auto-verifier 를 ~/repositories/auto-verifier 로 clone 하라.",
      accept:["git clone /repositories/auto-verifier ~/repositories/auto-verifier","git clone /repositories/auto-verifier /home/candidate/repositories/auto-verifier"],
      out:"Cloning into '/home/candidate/repositories/auto-verifier'...\ndone.",
      hint:"git clone <src> <dest>." },
    { q:"원격 브랜치까지 포함해 모든 브랜치를 나열하라.",
      accept:["git branch -a","git branch --all"],
      out:"* main\n  remotes/origin/dev4\n  remotes/origin/dev5\n  remotes/origin/dev6",
      hint:"git branch -a." },
    { q:"현재 브랜치(main)에 브랜치 dev5 를 병합하라.",
      accept:["git merge dev5","git merge origin/dev5"],
      out:"Updating 4084289..cdf23b8\nFast-forward\n config.yaml | 2 +-",
      hint:"git merge <branch>." },
    { q:"스테이징된 변경을 메시지 'added log directory' 로 커밋하라.",
      accept:["git commit -m \"added log directory\"","git commit -m 'added log directory'"],
      out:"[main 3cc53ed] added log directory\n 1 file changed, 0 insertions(+), 0 deletions(-)",
      hint:"git commit -m \"added log directory\"." },
    { q:"프로그램 output-generator 의 stdout 을 파일 1.out 으로 리다이렉트하라.",
      accept:["output-generator > 1.out","output-generator 1> 1.out"],
      out:"# stdout → 1.out",
      hint:"> 또는 1> 는 stdout 리다이렉트." },
    { q:"output-generator 의 stderr 를 파일 2.out 으로 리다이렉트하라.",
      accept:["output-generator 2> 2.out"],
      out:"# stderr → 2.out",
      hint:"2> 는 stderr 리다이렉트." },
    { q:"output-generator 의 stdout·stderr 를 모두 파일 3.out 으로 리다이렉트하라.",
      accept:["output-generator &> 3.out","output-generator > 3.out 2>&1","output-generator &>3.out"],
      out:"# stdout+stderr → 3.out",
      hint:"&> file 또는 > file 2>&1." },
    { q:"직전 명령의 종료 코드(exit code)를 출력하라.",
      accept:["echo $?"],
      out:"0",
      hint:"$? 에 직전 명령의 종료 코드가 담긴다." },
    { q:"server.log 에서 container.web 로 시작하고 Running 을 포함하며 24h 로 끝나는 줄을 'SENSITIVE LINE REMOVED' 로 치환(파일 직접 수정)하라.",
      accept:["sed -i 's/^container.web.*Running.*24h$/SENSITIVE LINE REMOVED/g' server.log","sed -i 's/^container.web.*Running.*24h$/SENSITIVE LINE REMOVED/' server.log"],
      out:"# 44개 줄이 치환됨",
      hint:"sed -i 's/^container.web.*Running.*24h$/SENSITIVE LINE REMOVED/g' server.log." }
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

  printBlock('Essential Commands 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
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

Essential Commands는 아카이브·`find`·Git·리다이렉션·정규식 등 일상 운영의 기본기이다.
`find`의 조건 조합과 `sed`·`grep`의 정규식은 손에 익혀 두면 활용도가 높다.
다음 편은 마지막 도메인 **Users and Groups** 를 다룬다.
