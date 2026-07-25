---
title: "LFCS 자격 준비 (3) Networking 실전 문제 + 연습 터미널"
date: 2026-07-22T10:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "Networking", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-03-networking-e856c7d0.png
---

LFCS 시리즈 세 번째 편으로 **Networking (25%)** 도메인을 다룬다.
시간 동기화, 패킷 필터링(iptables), 원격 파일시스템, 로드밸런서, OpenSSH가 핵심 주제이다.
정리 후 마지막의 **인터랙티브 연습 터미널**에서 명령을 직접 입력해 본다.

## 1. 시간 동기화

현재 시간·타임존·동기화 상태는 `timedatectl`로 한 번에 확인한다.
NTP 서버는 `/etc/systemd/timesyncd.conf`의 `NTP`(주 서버)와 `FallbackNTP`(대체)로 설정한다.
설정 후 `systemctl restart systemd-timesyncd`로 서비스를 재시작한다.

- **상태 확인**: `timedatectl`
- **설정 파일**: `/etc/systemd/timesyncd.conf` — `NTP=`, `FallbackNTP=`, `PollIntervalMaxSec=`, `ConnectionRetrySec=`

## 2. 패킷 필터링 (iptables)

필터 규칙은 `INPUT`/`OUTPUT`/`FORWARD` 체인에, NAT는 `-t nat`의 `PREROUTING` 등에 넣는다.
포트 차단은 `-j DROP`, 리다이렉트는 `REDIRECT --to-port`, 특정 IP 허용은 `-s`이다.

- **규칙 확인**: `iptables -L`, `iptables -L -t nat`
- **포트 차단**: `iptables -A INPUT -i eth0 -p tcp --dport 5000 -j DROP`
- **포트 리다이렉트**: `iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 6000 -j REDIRECT --to-port 6001`
- **아웃바운드 차단**: `iptables -A OUTPUT -d 192.168.10.70 -p tcp -j DROP`

## 3. 원격 파일시스템 (SSHFS·NFS)

SSHFS는 SSH 위에서 원격 디렉터리를 마운트한다(`allow_other`, `rw` 옵션).
NFS는 `/etc/exports`에 공유를 정의하고 `exportfs -ra`로 반영하며, 클라이언트에서 `mount`로 붙인다.

- **SSHFS**: `sshfs -o allow_other,rw app-srv1:/data-export /app-srv1/data-export`
- **NFS export**: `/etc/exports` → `exportfs -ra` → `showmount -e`
- **NFS mount**: `mount terminal:/nfs/share /nfs/terminal/share`

## 4. 로드밸런서 (Nginx)

Nginx로 리버스 프록시·로드밸런서를 만든다.
단일 대상은 `proxy_pass`, 여러 대상 분산은 `upstream` 블록을 쓴다.

```terminal
$ cat /etc/nginx/sites-available/lb
upstream backend {
    server 192.168.10.60:1111;
    server 192.168.10.60:2222;
}
server {
    listen 8000 default_server;
    location / { proxy_pass http://backend; }
}
$ service nginx restart
```

## 5. OpenSSH 설정

sshd 설정은 `/etc/ssh/sshd_config` 또는 드롭인 `/etc/ssh/sshd_config.d/*.conf`에 둔다.
유효 설정은 `sshd -T`로 확인하고, 사용자별 설정은 `Match User`로 재정의한다.

- **유효 설정 확인**: `sshd -T | grep -i x11forwarding`, `sshd -T -C user=marta`
- **사용자별 재정의**: `Match User marta` 아래에 `PasswordAuthentication yes` 등
- **재시작**: `service ssh restart`

## 연습 터미널 — Networking

문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help` 사용법, `hint` 힌트, `skip` 건너뛰기, `clear` 화면 지우기를 쓸 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Networking</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

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
    { q:"현재 시간·타임존·NTP 동기화 상태를 한 번에 확인하라.",
      accept:["timedatectl"],
      out:"               Local time: Sun 2023-06-11 16:29:05 UTC\n                Time zone: UTC (UTC, +0000)\nSystem clock synchronized: yes\n              NTP service: active",
      hint:"timedatectl 명령 하나로 확인한다." },
    { q:"systemd-timesyncd 설정 파일의 내용을 확인하라.",
      accept:["cat /etc/systemd/timesyncd.conf","less /etc/systemd/timesyncd.conf"],
      out:"[Time]\nNTP=0.pool.ntp.org 1.pool.ntp.org\nFallbackNTP=ntp.ubuntu.com 0.debian.pool.ntp.org",
      hint:"설정은 /etc/systemd/timesyncd.conf 에 있다." },
    { q:"systemd-timesyncd 서비스를 재시작하라.",
      accept:["systemctl restart systemd-timesyncd","service systemd-timesyncd restart","sudo systemctl restart systemd-timesyncd","sudo service systemd-timesyncd restart"],
      out:"# systemd-timesyncd 재시작됨",
      hint:"systemctl restart systemd-timesyncd 또는 service ... restart." },
    { q:"현재 iptables 필터 규칙을 확인하라.",
      accept:["iptables -L","sudo iptables -L"],
      out:"Chain INPUT (policy ACCEPT)\ntarget  prot opt source     destination\nChain OUTPUT (policy ACCEPT)",
      hint:"iptables -L (NAT는 -L -t nat)." },
    { q:"eth0로 들어오는 tcp 포트 5000 을 차단(DROP)하라.",
      accept:["iptables -A INPUT -i eth0 -p tcp --dport 5000 -j DROP","sudo iptables -A INPUT -i eth0 -p tcp --dport 5000 -j DROP"],
      out:"# INPUT 체인에 5000 DROP 규칙 추가됨",
      hint:"iptables -A INPUT -i eth0 -p tcp --dport 5000 -j DROP" },
    { q:"eth0의 tcp 포트 6000 트래픽을 로컬 포트 6001 로 리다이렉트하라.",
      accept:["iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 6000 -j REDIRECT --to-port 6001","iptables -A PREROUTING -i eth0 -t nat -p tcp --dport 6000 -j REDIRECT --to-port 6001","sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 6000 -j REDIRECT --to-port 6001"],
      out:"# nat PREROUTING 에 6000→6001 REDIRECT 추가됨",
      hint:"nat 테이블 PREROUTING 체인에 REDIRECT --to-port 6001." },
    { q:"목적지 IP 192.168.10.70 으로 나가는 tcp 트래픽을 차단하라.",
      accept:["iptables -A OUTPUT -d 192.168.10.70 -p tcp -j DROP","sudo iptables -A OUTPUT -d 192.168.10.70 -p tcp -j DROP"],
      out:"# OUTPUT 체인에 192.168.10.70 DROP 규칙 추가됨",
      hint:"iptables -A OUTPUT -d <IP> -p tcp -j DROP" },
    { q:"NAT 테이블의 규칙을 확인하라.",
      accept:["iptables -L -t nat","iptables -t nat -L","sudo iptables -L -t nat"],
      out:"Chain PREROUTING (policy ACCEPT)\nREDIRECT  tcp -- anywhere  anywhere  tcp dpt:6000 redir ports 6001",
      hint:"iptables -L -t nat." },
    { q:"app-srv1:/data-export 를 /app-srv1/data-export 에 rw·allow_other 로 SSHFS 마운트하라.",
      accept:["sshfs -o allow_other,rw app-srv1:/data-export /app-srv1/data-export","sudo sshfs -o allow_other,rw app-srv1:/data-export /app-srv1/data-export","sshfs -o rw,allow_other app-srv1:/data-export /app-srv1/data-export"],
      out:"# SSHFS 마운트 완료 (rw, allow_other)",
      hint:"sshfs -o allow_other,rw 원격:경로 로컬경로" },
    { q:"NFS export 설정을 다시 읽어들여 모두 반영하라.",
      accept:["exportfs -ra","sudo exportfs -ra"],
      out:"# /etc/exports 재적용 완료",
      hint:"exportfs -ra ( -r 재export, -a 전체)." },
    { q:"NFS 서버가 export 하는 공유 목록을 확인하라.",
      accept:["showmount -e","sudo showmount -e"],
      out:"Export list for terminal:\n/nfs/share  192.168.10.0/24",
      hint:"showmount -e." },
    { q:"sshd의 유효 설정에서 X11Forwarding 값을 확인하라.",
      accept:["sshd -T | grep -i x11forwarding","sshd -T | grep x11forwarding","sudo sshd -T | grep -i x11forwarding"],
      out:"x11forwarding no",
      hint:"sshd -T 로 유효 설정을 출력하고 grep 으로 필터." },
    { q:"사용자 marta 기준으로 sshd 유효 설정을 확인하라(banner 값 등).",
      accept:["sshd -T -C user=marta","sudo sshd -T -C user=marta","sshd -T -C user=marta | grep banner"],
      out:"banner /etc/ssh/sshd-banner",
      hint:"sshd -T -C user=<name> 으로 사용자별 유효 설정 확인." },
    { q:"ssh(sshd) 서비스를 재시작하라.",
      accept:["service ssh restart","systemctl restart ssh","systemctl restart sshd","sudo service ssh restart","sudo systemctl restart ssh"],
      out:"# ssh 서비스 재시작됨",
      hint:"service ssh restart 또는 systemctl restart ssh." }
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

  printBlock('Networking 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
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

Networking은 시간 동기화, 패킷 필터링, 원격 파일시스템, 로드밸런서, OpenSSH까지 폭넓게 다룬다.
설정 파일 위치와 `iptables`·`sshd -T` 같은 확인 명령을 함께 외워 두면 좋다.
다음 편은 **Storage** 도메인의 생성·수정 작업을 다룬다.
