---
title: "LFCS 자격 준비 (2) Operations Deployment 실전 문제 + 연습 터미널"
date: 2026-07-22T09:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-02-operations-deployment-e4a033fd.png
---

LFCS 시리즈의 두 번째 편으로, 비중이 가장 큰 **Operations Deployment (25%)** 도메인을 다룬다.
커널 정보, CronJob, 컨테이너, 프로세스 진단, 소스 빌드가 핵심 주제이다.
각 주제를 정리한 뒤, 마지막에 **인터랙티브 연습 터미널**로 명령을 직접 입력해 본다.

## 1. Kernel·시스템 정보

커널 릴리스는 `uname -r`로 확인한다.
커널 파라미터는 `/proc/sys/` 아래 파일이나 `sysctl`로 읽으며, 영구 설정은 `/etc/sysctl.d/*.conf`에 둔다.
타임존은 `timedatectl`, `date +%Z`, `/etc/timezone`으로 확인한다.

- **커널 릴리스**: `uname -r`
- **커널 파라미터 조회**: `cat /proc/sys/net/ipv4/ip_forward` 또는 `sysctl net.ipv4.ip_forward`
- **타임존**: `date +%Z`, `cat /etc/timezone`

## 2. CronJob

시스템 전역 cron은 `/etc/crontab`에 있으며 **user 필드**를 포함한다.
사용자 cron은 `crontab -e`로 편집하고 `crontab -l`로 확인하며, user 필드가 없다.
시간 필드는 **분 시 일 월 요일** 순서이다.

- **사용자 cron 편집·목록**: `crontab -e` / `crontab -l`
- **월·목 11:15 실행**: `15 11 * * 1,4` (요일명은 `mon,thu`도 가능)
- **사용자 crontab 저장 위치**: `/var/spool/cron/crontabs`

## 3. Docker 컨테이너

컨테이너 목록은 `docker ps`(중지 포함은 `-a`), 중지는 `docker stop`이다.
상세 정보(IP·마운트)는 `docker inspect`로 JSON을 확인한다.
새 컨테이너는 `docker run`에 옵션을 조합한다.

- **목록·중지**: `docker ps` / `docker stop <name>`
- **상세**: `docker inspect <name>` → `IPAddress`, `Mounts[].Destination`
- **실행**: `docker run -d --name N --memory 30m -p 1234:80 nginx:alpine`

## 4. 프로세스 진단

실행 중 프로세스는 `ps aux`로 찾아 grep으로 필터한다.
특정 PID의 시스템 콜(syscall)은 `strace -p <PID>`로 추적한다.
종료는 `kill <PID>`, 실행 파일 경로는 `ps`의 COMMAND나 `/proc/<PID>/exe`로 확인한다.

## 5. 소스 빌드·설치

소스 설치는 보통 `./configure` → `make` → `make install` 순서로 진행한다.
bzip2로 압축된 tar는 `tar xjf`로 푼다.
`./configure`의 `--prefix`로 설치 위치를, `--without-ipv6` 같은 옵션으로 기능을 끈다.

```terminal
$ tar xjf links-2.14.tar.bz2
$ cd links-2.14
$ ./configure --prefix /usr --without-ipv6
Configuration results:
IPv6:  NO
$ make && make install
```

## 연습 터미널 — Operations Deployment

문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help` 사용법, `hint` 힌트, `skip` 건너뛰기, `clear` 화면 지우기를 쓸 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Operations Deployment</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

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
    { q:"커널 릴리스(kernel release) 버전을 출력하라.",
      accept:["uname -r"],
      out:"5.15.0-69-generic",
      hint:"uname 명령에 -r(release) 옵션을 붙인다." },
    { q:"커널 파라미터 net.ipv4.ip_forward 의 현재 값을 출력하라.",
      accept:["cat /proc/sys/net/ipv4/ip_forward","sysctl net.ipv4.ip_forward","sysctl -n net.ipv4.ip_forward"],
      out:"1",
      hint:"/proc/sys/net/ipv4/ip_forward 파일을 cat 하거나 sysctl 로 조회한다." },
    { q:"시스템 타임존(timezone)을 확인하라.",
      accept:["date +%Z","cat /etc/timezone","timedatectl"],
      out:"UTC",
      hint:"date +%Z 또는 cat /etc/timezone 을 쓴다." },
    { q:"시스템 전역 cron 설정 파일의 내용을 확인하라.",
      accept:["cat /etc/crontab","less /etc/crontab","more /etc/crontab"],
      out:"# m h dom mon dow user  command\n17 *  * * * root  cd / && run-parts --report /etc/cron.hourly\n30 20 * * * root  bash /home/asset-manager/generate.sh",
      hint:"시스템 전역 크론탭은 /etc/crontab 에 있고 user 필드를 포함한다." },
    { q:"현재 사용자(asset-manager)의 개인 crontab 목록을 출력하라.",
      accept:["crontab -l"],
      out:"30 20 * * * bash /home/asset-manager/generate.sh",
      hint:"crontab 명령에 -l(list) 옵션을 붙인다." },
    { q:"매주 월요일·목요일 11시 15분에 실행하는 cron 시간식을 입력하라. (5개 필드만, 명령 제외)",
      accept:["15 11 * * 1,4","15 11 * * mon,thu"],
      out:"OK  분 시 일 월 요일 = 15 11 * * 1,4  (월=1, 목=4)",
      hint:"분 시 일 월 요일 순서. 월=1, 목=4 → 15 11 * * 1,4" },
    { q:"실행 중인 Docker 컨테이너 목록을 출력하라.",
      accept:["docker ps","sudo docker ps"],
      out:"CONTAINER ID   IMAGE          STATUS          NAMES\na9b334cfaae0   nginx:alpine   Up 11 minutes   frontend_v1\ne68fa28f231d   nginx:alpine   Up 7 minutes    frontend_v2",
      hint:"docker ps (중지된 것 포함은 -a)." },
    { q:"컨테이너 frontend_v1 을 중지하라.",
      accept:["docker stop frontend_v1","sudo docker stop frontend_v1"],
      out:"frontend_v1",
      hint:"docker stop <name>." },
    { q:"컨테이너 frontend_v2 의 상세 정보(IP·마운트)를 확인하라.",
      accept:["docker inspect frontend_v2","sudo docker inspect frontend_v2"],
      out:"\"IPAddress\": \"172.17.0.3\",\n\"Destination\": \"/srv\",",
      hint:"docker inspect <name> — IPAddress, Mounts[].Destination 를 확인한다." },
    { q:"nginx:alpine 이미지로 이름 frontend_v3, 메모리 30m, 호스트 1234→컨테이너 80 포트, 백그라운드(detached)로 컨테이너를 실행하라.",
      accept:["docker run -d --name frontend_v3 --memory 30m -p 1234:80 nginx:alpine","sudo docker run -d --name frontend_v3 --memory 30m -p 1234:80 nginx:alpine"],
      out:"1e7d4612df4a...   # frontend_v3 시작됨",
      hint:"docker run -d --name frontend_v3 --memory 30m -p 1234:80 nginx:alpine" },
    { q:"이름에 collector 가 들어간 실행 중 프로세스를 확인하라.",
      accept:["ps aux | grep collector","ps -ef | grep collector"],
      out:"root  3611  ... /bin/collector1\nroot  3612  ... /bin/collector2\nroot  3613  ... /bin/collector3",
      hint:"ps aux 를 grep 으로 필터한다." },
    { q:"PID 3612 프로세스의 시스템 콜(syscall)을 추적하라.",
      accept:["strace -p 3612","sudo strace -p 3612"],
      out:"kill(666, SIGTERM) = -1 ESRCH (No such process)   # 금지된 kill syscall 발견",
      hint:"strace -p <PID> 로 실행 중 프로세스를 추적한다." },
    { q:"bzip2 로 압축된 소스 아카이브 links-2.14.tar.bz2 를 현재 위치에 추출하라.",
      accept:["tar xjf links-2.14.tar.bz2","tar -xjf links-2.14.tar.bz2","tar xf links-2.14.tar.bz2"],
      out:"# 압축 해제 완료 → links-2.14/ 디렉터리 생성",
      hint:"tar 의 x(추출) j(bzip2) f(파일) 옵션을 쓴다." },
    { q:"설치 접두사(prefix)를 /usr 로, ipv6 를 비활성화하여 빌드 설정(configure)하라.",
      accept:["./configure --prefix /usr --without-ipv6","./configure --prefix=/usr --without-ipv6"],
      out:"Configuration results:\nIPv6:  NO\ncreating Makefile",
      hint:"./configure --prefix /usr --without-ipv6 (이후 make && make install)." }
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

  printBlock('Operations Deployment 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
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

Operations Deployment는 커널·프로세스·컨테이너·소스 빌드 등 시스템 운영 전반을 다루며 비중이 가장 크다.
명령 하나하나를 손에 익히는 것이 실기 시험의 핵심이다.
다음 편은 **Networking** 도메인의 실전 문제를 같은 방식으로 다룬다.
