---
title: "LFCS 자격 준비 (4) Storage 생성·수정 실전 문제 + 연습 터미널"
date: 2026-07-22T11:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "Storage", "LVM", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-04-storage-operations-b86f7963.png
---

LFCS 시리즈 네 번째 편으로 **Storage (20%)** 도메인의 **생성·수정 작업**을 다룬다.
1편이 `lsblk`·`df`·`pvs` 같은 **조회** 위주였다면, 이번 편은 포맷·마운트·LVM 변경 같은 **실제 작업**이 중심이다.
정리 후 **인터랙티브 연습 터미널**에서 명령을 직접 입력해 본다.

## 1. 디스크 포맷·마운트

새 디스크는 `mkfs`로 파일시스템을 만든 뒤 `mount`로 붙인다.
디스크 목록은 `fdisk -l`·`lsblk -f`, 사용량은 `df -h`로 확인한다.

- **포맷**: `mkfs -t ext4 /dev/vdb`
- **마운트**: `mount /dev/vdb /mnt/backup-black`
- **파일 생성**: `touch /mnt/backup-black/completed`

## 2. 언마운트와 사용 중 프로세스

언마운트 시 `target is busy`가 나오면 해당 경로를 잡고 있는 프로세스가 있다.
`lsof`로 범인을 찾아 종료한 뒤 `umount`한다.

- **사용 프로세스 확인**: `lsof | grep /mnt/app-4e9d7e1e`
- **언마운트**: `umount /mnt/app-4e9d7e1e`

## 3. LVM 변경

LVM은 **PV(물리 볼륨) → VG(볼륨 그룹) → LV(논리 볼륨)** 구조이다.
VG에서 디스크를 빼려면 `vgreduce`, 새 VG는 `vgcreate`, LV는 `lvcreate`로 만든다.
크기 변경은 `lvresize`(또는 `lvextend`)를 쓴다.

- **VG에서 PV 제거**: `vgreduce vol1 /dev/vdh`
- **VG 생성**: `vgcreate vol2 /dev/vdh`
- **LV 생성**: `lvcreate --size 50M --name p1 vol2`
- **LV 포맷**: `mkfs -t ext4 /dev/vol2/p1`

```terminal
$ vgreduce vol1 /dev/vdh
$ vgcreate vol2 /dev/vdh
$ lvcreate --size 50M --name p1 vol2
$ mkfs -t ext4 /dev/vol2/p1
```

## 연습 터미널 — Storage

문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help` 사용법, `hint` 힌트, `skip` 건너뛰기, `clear` 화면 지우기를 쓸 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Storage 작업</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

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
    { q:"연결된 모든 디스크를 상세히 나열하라.",
      accept:["fdisk -l","sudo fdisk -l"],
      out:"Disk /dev/vdb: 100 MiB, 104857600 bytes, 204800 sectors\nDisk /dev/vdc: 100 MiB, ...\nDisk /dev/vdd: 100 MiB, ...",
      hint:"fdisk -l (또는 lsblk)." },
    { q:"파일시스템 타입·마운트 지점을 트리 형태로 확인하라.",
      accept:["lsblk -f","lsblk"],
      out:"NAME  FSTYPE  MOUNTPOINTS\nvdb\nvdc   ext4    /mnt/backup001\nvdd   ext4    /mnt/backup002",
      hint:"lsblk -f 는 파일시스템 정보까지 보여준다." },
    { q:"디스크 /dev/vdb 를 ext4 파일시스템으로 포맷하라.",
      accept:["mkfs -t ext4 /dev/vdb","mkfs.ext4 /dev/vdb","sudo mkfs -t ext4 /dev/vdb","sudo mkfs.ext4 /dev/vdb"],
      out:"mke2fs 1.46.5 (30-Dec-2021)\nCreating filesystem with 25600 4k blocks and 25600 inodes\ndone",
      hint:"mkfs -t ext4 /dev/vdb 또는 mkfs.ext4 /dev/vdb." },
    { q:"/dev/vdb 를 /mnt/backup-black 에 마운트하라.",
      accept:["mount /dev/vdb /mnt/backup-black","sudo mount /dev/vdb /mnt/backup-black"],
      out:"# /dev/vdb → /mnt/backup-black 마운트됨",
      hint:"mount <device> <mountpoint>." },
    { q:"/mnt/backup-black/completed 빈 파일을 생성하라.",
      accept:["touch /mnt/backup-black/completed","sudo touch /mnt/backup-black/completed"],
      out:"# 빈 파일 completed 생성됨",
      hint:"touch <path>." },
    { q:"마운트 지점별 디스크 사용량을 사람이 읽기 쉬운 단위로 확인하라.",
      accept:["df -h"],
      out:"Filesystem  Size  Used Avail Use% Mounted on\n/dev/vdc     90M   51M   33M  61% /mnt/backup001\n/dev/vdd     90M  5.1M   78M   7% /mnt/backup002",
      hint:"df -h." },
    { q:"경로 /mnt/app-4e9d7e1e 를 사용 중인 프로세스를 찾아라. (언마운트가 busy일 때)",
      accept:["lsof | grep /mnt/app-4e9d7e1e","sudo lsof | grep /mnt/app-4e9d7e1e"],
      out:"dark-matt 6204 root txt REG ... /mnt/app-4e9d7e1e/dark-matter-v2",
      hint:"lsof 로 열린 파일을 나열하고 grep 으로 경로 필터." },
    { q:"/mnt/app-4e9d7e1e 를 언마운트하라.",
      accept:["umount /mnt/app-4e9d7e1e","sudo umount /mnt/app-4e9d7e1e"],
      out:"# 언마운트 완료",
      hint:"umount <mountpoint> (프로세스가 잡고 있으면 먼저 kill)." },
    { q:"LVM 물리 볼륨(PV) 목록을 확인하라.",
      accept:["pvs","sudo pvs","pvdisplay"],
      out:"PV        VG    Fmt  Attr PSize  PFree\n/dev/vdg  vol1  lvm2 a--  96.00m 84.00m\n/dev/vdh  vol1  lvm2 a--  96.00m 96.00m",
      hint:"pvs 로 물리 볼륨을 요약해서 본다." },
    { q:"볼륨 그룹 vol1 에서 물리 볼륨 /dev/vdh 를 제거하라.",
      accept:["vgreduce vol1 /dev/vdh","sudo vgreduce vol1 /dev/vdh"],
      out:'Removed "/dev/vdh" from volume group "vol1"',
      hint:"vgreduce <VG> <PV>." },
    { q:"디스크 /dev/vdh 로 새 볼륨 그룹 vol2 를 생성하라.",
      accept:["vgcreate vol2 /dev/vdh","sudo vgcreate vol2 /dev/vdh"],
      out:'Volume group "vol2" successfully created',
      hint:"vgcreate <newVG> <PV>." },
    { q:"볼륨 그룹 vol2 에 크기 50M, 이름 p1 인 논리 볼륨을 생성하라.",
      accept:["lvcreate --size 50M --name p1 vol2","lvcreate -L 50M -n p1 vol2","sudo lvcreate --size 50M --name p1 vol2","sudo lvcreate -L 50M -n p1 vol2"],
      out:'Rounding up size to full physical extent 52.00 MiB\nLogical volume "p1" created.',
      hint:"lvcreate --size 50M --name p1 vol2 (또는 -L/-n)." },
    { q:"논리 볼륨 /dev/vol2/p1 을 ext4 로 포맷하라.",
      accept:["mkfs -t ext4 /dev/vol2/p1","mkfs.ext4 /dev/vol2/p1","sudo mkfs -t ext4 /dev/vol2/p1"],
      out:"mke2fs 1.46.5 (30-Dec-2021)\nCreating filesystem with 13312 4k blocks\ndone",
      hint:"mkfs -t ext4 /dev/vol2/p1." },
    { q:"논리 볼륨 vol2/p1 의 크기를 70M 로 확장하라.",
      accept:["lvresize vol2/p1 --size 70M","lvresize -L 70M vol2/p1","lvextend -L 70M /dev/vol2/p1","sudo lvresize -L 70M vol2/p1","sudo lvextend -L 70M /dev/vol2/p1"],
      out:"Size of logical volume vol2/p1 changed from 52.00 MiB to 72.00 MiB.\nLogical volume vol2/p1 successfully resized.",
      hint:"lvresize --size 70M vol2/p1 또는 lvextend -L 70M /dev/vol2/p1." }
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

  printBlock('Storage 작업 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
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

Storage 작업은 포맷·마운트·언마운트와 LVM(PV·VG·LV) 관리가 핵심이다.
조회 명령(1편)과 작업 명령(이번 편)을 함께 익히면 시험에서 흔들리지 않는다.
다음 편은 **Essential Commands** 도메인을 다룬다.
