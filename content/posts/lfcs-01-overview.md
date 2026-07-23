---
title: "LFCS 자격 준비 (1) 시험 개요와 도메인 정리 + Storage 연습 터미널"
date: 2026-07-21T09:00:00+09:00
draft: false
tags: ["LFCS", "Linux", "System Administration", "자격시험"]
categories: ["자격시험"]
featuredImage: images/banners/lfcs-01-overview-792ebc6b.png
---

**LFCS(Linux Foundation Certified System Administrator)** 는 실제 터미널에서 작업을 수행하는 **실기(hands-on)** 시험이다.
객관식이 아니라 주어진 과제를 명령으로 직접 해결하는 방식이므로, 명령어를 손에 익히는 연습이 중요하다.
이 글은 시험 도메인 전체를 정리하고, 마지막에 **Storage 도메인 연습 터미널**을 제공한다.

## 시험 개요

LFCS는 5개 도메인으로 구성되며, 비중은 다음과 같다.

| 도메인 | 비중 |
|---|---|
| Operations Deployment | 25% |
| Networking | 25% |
| Storage | 20% |
| Essential Commands | 20% |
| Users and Groups | 10% |

각 도메인의 세부 역량과 핵심 명령을 아래에 정리한다.

## Operations Deployment (25%)

시스템 배포·운영 전반을 다루며 비중이 가장 크다.
kernel 파라미터, 프로세스·서비스, 패키지, 컨테이너, SELinux가 핵심이다.

- **kernel 파라미터**: `sysctl -a`로 조회, 비영구는 `sysctl -w`, 영구는 `/etc/sysctl.d/*.conf`
- **프로세스·서비스**: `ps`, `top`, `systemctl`, `journalctl`, `kill`, `renice`
- **job 스케줄**: `crontab -e`, `systemd timer`, 일회성은 `at`
- **패키지·저장소**: `dnf`/`apt`, `rpm`, 저장소는 `/etc/yum.repos.d/`
- **장애 복구**: `grub`, rescue mode, `fsck`
- **가상머신(libvirt)**: `virsh`, `virt-install`
- **컨테이너**: `podman run`/`ps`/`build`
- **SELinux(MAC)**: `getenforce`, `setenforce`, `semanage`, `restorecon`, `sestatus`

## Networking (25%)

네트워크 설정과 트러블슈팅을 다룬다.
현대 RHEL 계열에서는 대부분 **NetworkManager(`nmcli`)** 로 설정한다.

- **IPv4/IPv6·이름해석**: `nmcli`, `ip addr`, `/etc/hosts`, `/etc/resolv.conf`, `hostnamectl`
- **시간 동기화**: `timedatectl`, `chronyd`, `/etc/chrony.conf`
- **모니터링·트러블슈팅**: `ip`, `ss`, `ping`, `traceroute`, `tcpdump`, `dig`
- **OpenSSH**: `/etc/ssh/sshd_config`, `ssh-keygen`, `~/.ssh/authorized_keys`
- **패킷 필터링·NAT**: `firewall-cmd`, `nftables`, port forward, masquerade
- **정적 라우팅**: `ip route`, `nmcli connection` route
- **bridge·bonding**: `nmcli`로 bond·bridge 생성
- **reverse proxy·LB**: `nginx`, `haproxy`

## Storage (20%)

저장소 구성과 파일시스템을 다루며, 이번 편의 연습 대상이다.
LVM, 파일시스템, swap, mount·automount가 핵심이다.

- **LVM**: `pvcreate`/`vgcreate`/`lvcreate`, 조회는 `pvs`/`vgs`/`lvs`, 확장은 `lvextend` + `resize2fs`
- **가상 파일시스템**: `/proc`, `/sys`
- **파일시스템**: `mkfs.xfs`/`mkfs.ext4`, `mount`, `/etc/fstab`, `fsck`, `xfs_repair`, `blkid`, `lsblk`
- **원격 fs·네트워크 블록 장치**: `mount -t nfs`, `iscsi`, `nbd`
- **swap**: `mkswap`, `swapon`, `swapoff`, `swapon --show`, `free -h`
- **automounter**: `autofs`, `/etc/auto.master`
- **성능 모니터링**: `iostat`, `df -h`, `df -i`, `du`

명령 출력 형태를 미리 익혀 두면 좋다.

```terminal
$ lsblk
NAME   SIZE TYPE MOUNTPOINT
sda     20G disk
├─sda1  18G part /
└─sda2   2G part [SWAP]
$ free -h
              total   used   free
Mem:           1.9G   420M   1.1G
Swap:          2.0G     0B   2.0G
```

## Essential Commands (20%)

일상 운영에 필요한 기본 도구를 다룬다.

- **Git 기본**: `git clone`/`add`/`commit`/`push`/`pull`/`branch`/`merge`
- **서비스**: `systemctl`, unit 파일 `/etc/systemd/system/`, 변경 후 `daemon-reload`
- **성능 모니터링**: `top`, `vmstat`, `iostat`, `sar`, `journalctl`
- **애플리케이션 제약**: `ulimit`, cgroup
- **디스크공간 트러블슈팅**: `df`, `du`, inode 고갈은 `df -i`
- **SSL 인증서**: `openssl`로 키·CSR 생성, 인증서 확인

## Users and Groups (10%)

계정과 권한을 다루며 비중은 가장 작다.

- **사용자·그룹**: `useradd`, `usermod`, `groupadd`, `passwd`, `/etc/passwd`, `/etc/group`
- **환경 프로필**: `/etc/profile`, `~/.bashrc`, `/etc/profile.d/`
- **리소스 제한**: `/etc/security/limits.conf`, `ulimit`
- **ACL**: `getfacl`, `setfacl`
- **LDAP 연동**: `sssd`, `/etc/sssd/sssd.conf`, `authselect`

## 연습 터미널 — Storage

아래는 **Storage 도메인 연습 터미널**이다.
제시된 문제를 읽고 알맞은 명령을 입력하면, 정답일 때 정해진 출력과 함께 다음 문제로 넘어간다.
`help`로 사용법, `hint`로 힌트, `skip`으로 건너뛰기, `clear`로 화면 지우기를 할 수 있다.

<div id="lfx-term" class="lfx-term"><div class="lfx-bar"><span class="lfx-dot lfx-red"></span><span class="lfx-dot lfx-yellow"></span><span class="lfx-dot lfx-green"></span><span class="lfx-title">lfcs@exam: ~ — Storage 연습</span></div><div id="lfx-body" class="lfx-body"><div id="lfx-output" class="lfx-output"></div><div class="lfx-line"><span class="lfx-prompt">lfcs@exam:~$</span><input id="lfx-input" class="lfx-input" type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="terminal input" /></div></div></div>

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
  // ==============================
  //  연습 문제 정의 — 이 배열만 수정하면 됩니다.
  //  accept: 정답으로 인정할 명령들(공백은 자동 정규화)
  //  out   : 정답일 때 보여줄 정해진 출력(HTML 허용)
  //  hint  : 오답 시 'hint' 로 볼 수 있는 힌트
  // ==============================
  var PROBLEMS = [
    { q:"블록 디바이스(디스크·파티션)를 트리 형태로 나열하라.",
      accept:["lsblk"],
      out:"NAME   SIZE TYPE MOUNTPOINT\nsda     20G disk\n├─sda1  18G part /\n└─sda2   2G part [SWAP]",
      hint:"블록 디바이스를 나열하는 전용 명령이다. 'ls'로 시작하지 않는다." },
    { q:"현재 활성화된 swap 공간을 확인하라.",
      accept:["swapon --show","swapon -s","cat /proc/swaps"],
      out:"NAME      TYPE       SIZE USED PRIO\n/dev/sda2 partition    2G   0B   -2",
      hint:"swapon 명령에 --show 옵션을 붙인다." },
    { q:"메모리와 swap 사용량을 사람이 읽기 쉬운 단위로 확인하라.",
      accept:["free -h","free -m","free"],
      out:"              total   used   free\nMem:           1.9G   420M   1.1G\nSwap:          2.0G     0B   2.0G",
      hint:"메모리 사용량 명령에 -h(human-readable) 옵션을 붙인다." },
    { q:"마운트된 파일시스템의 여유 용량을 사람이 읽기 쉬운 단위로 확인하라.",
      accept:["df -h"],
      out:"Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        18G  6.2G   11G  37% /\ntmpfs           952M     0  952M   0% /dev/shm",
      hint:"디스크 여유공간 명령에 -h 옵션을 붙인다." },
    { q:"inode 사용량을 확인하라. (파일 개수 고갈 진단)",
      accept:["df -i"],
      out:"Filesystem     Inodes IUsed  IFree IUse% Mounted on\n/dev/sda1      1.2M   82K   1.1M    7% /",
      hint:"디스크 사용량 명령에 -i(inode) 옵션을 붙인다." },
    { q:"각 파티션의 UUID와 파일시스템 타입을 확인하라.",
      accept:["blkid"],
      out:"/dev/sda1: UUID=\"a1b2-c3d4\" TYPE=\"xfs\"\n/dev/sda2: UUID=\"e5f6-7890\" TYPE=\"swap\"",
      hint:"블록 디바이스의 속성(UUID/TYPE)을 출력하는 명령이다. 'blk'로 시작한다." },
    { q:"LVM 물리 볼륨(PV) 목록을 확인하라.",
      accept:["pvs","pvdisplay"],
      out:"PV         VG     Fmt  Attr PSize  PFree\n/dev/sda3  vg_data lvm2 a--  18.00g 4.00g",
      hint:"LVM physical volume을 요약해서 보여주는 짧은 명령이다." },
    { q:"LVM 볼륨 그룹(VG) 목록을 확인하라.",
      accept:["vgs","vgdisplay"],
      out:"VG      #PV #LV #SN Attr   VSize  VFree\nvg_data   1   2   0 wz--n- 18.00g 4.00g",
      hint:"LVM volume group을 요약해서 보여주는 짧은 명령이다." },
    { q:"LVM 논리 볼륨(LV) 목록을 확인하라.",
      accept:["lvs","lvdisplay"],
      out:"LV      VG      Attr       LSize\nlv_home vg_data -wi-ao----  6.00g\nlv_root vg_data -wi-ao----  8.00g",
      hint:"LVM logical volume을 요약해서 보여주는 짧은 명령이다." },
    { q:"/etc/fstab 내용을 확인하라. (부팅 시 마운트 설정)",
      accept:["cat /etc/fstab","less /etc/fstab","more /etc/fstab"],
      out:"UUID=a1b2-c3d4  /      xfs   defaults        0 0\nUUID=e5f6-7890  none   swap  sw              0 0",
      hint:"파일 내용을 출력하는 명령 뒤에 /etc/fstab 경로를 붙인다." }
  ];

  var body = document.getElementById("lfx-body");
  var output = document.getElementById("lfx-output");
  var input = document.getElementById("lfx-input");
  if(!body || !output || !input){ return; }

  var idx = 0;
  var solved = 0;
  var history = [];
  var hIndex = -1;

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
    var p = PROBLEMS[idx];
    printBlock('<span class="lfx-q">[문제 ' + (idx+1) + '/' + PROBLEMS.length + '] ' + p.q + '</span>');
  }

  function run(raw){
    var cmd = normalize(raw);
    echoCommand(raw);
    if(cmd !== ""){ history.push(cmd); hIndex = history.length; }

    // 전역 명령
    if(cmd === "clear"){ output.innerHTML = ""; showProblem(); return; }
    if(cmd === "help"){
      printBlock("연습 방법:\n  문제를 읽고 알맞은 명령을 입력한다.\n  <span class=\"lfx-key\">hint</span>  힌트 보기    <span class=\"lfx-key\">skip</span>  건너뛰기\n  <span class=\"lfx-key\">clear</span> 화면 지우기  <span class=\"lfx-key\">reset</span> 처음부터");
      return;
    }
    if(cmd === "reset"){ idx = 0; solved = 0; output.innerHTML = ""; printBlock('처음부터 다시 시작한다.'); showProblem(); return; }
    if(idx >= PROBLEMS.length){ printBlock('이미 모든 문제를 마쳤다. <span class="lfx-key">reset</span> 을 입력하라.'); return; }

    var p = PROBLEMS[idx];
    if(cmd === "hint"){ printBlock('<span class="lfx-hint">힌트: ' + p.hint + '</span>'); return; }
    if(cmd === "skip"){ printBlock('<span class="lfx-err">건너뛴다. 정답 예시: ' + p.accept[0] + '</span>'); idx++; showProblem(); return; }
    if(cmd === ""){ return; }

    // 정답 판정
    var ok = p.accept.some(function(a){ return normalize(a) === cmd; });
    if(ok){
      printBlock(p.out);
      printBlock('<span class="lfx-ok">✔ 정답!</span>');
      solved++;
      idx++;
      showProblem();
    } else {
      printBlock('<span class="lfx-err">✘ 예상한 명령이 아니다.</span> <span class="lfx-key">hint</span> 로 힌트를, <span class="lfx-key">skip</span> 으로 정답을 볼 수 있다.');
    }
  }

  // 시작 안내
  printBlock('Storage 연습 터미널이다. 출력값은 학습용으로 <span class="lfx-hint">미리 정의된 값</span>이다(실제 시스템 아님).\n<span class="lfx-key">help</span> 로 사용법을 볼 수 있다.');
  showProblem();

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

  body.addEventListener("click", function(){ input.focus(); });
})();
</script>

## 정리

LFCS는 5개 도메인의 실기 시험이며, 명령을 직접 다루는 감각이 합격의 핵심이다.
이번 편은 전체 도메인을 정리하고 Storage 연습 터미널로 명령 출력 형태를 익혔다.
다음 편부터는 도메인별로 자주 나오는 작업을 연습 문제와 함께 다룬다.
