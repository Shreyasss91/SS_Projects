# PC Slowness — Diagnosis, Analysis & Upgrade Report

**Machine:** HP Notebook (board `80C3`), Insyde BIOS `F.02` (2015-03-24)
**Investigated:** 2026-08-05
**Investigated by:** Claude Code, non-elevated session
**Deliverables in this folder:** this report + [`pc-cleanup.ps1`](./pc-cleanup.ps1)

> You typed "report.ms" — I assumed you meant `report.md` (Markdown). This is that file.

> **Just want the answer?** Read **[Plain English — read this first](#plain-english--read-this-first)**
> below. Everything after §0 is the technical evidence behind it.

---

## Plain English — read this first

*No jargon. Everything here is explained in full detail later; section numbers point you there.*

### The main cause: your hard disk is old, slow, and mechanically worn out

- **It's a spinning disk, not an SSD.** Inside it are actual metal platters spinning at 5400 RPM,
  with a tiny arm reaching across them to find your data. Every time Windows opens a file, that arm
  physically moves. It is roughly **100× slower** than a modern SSD. This is a tax on *everything* —
  booting, opening Chrome, saving a file, all of it. *(§2.2)*
- **It has been running for 25,005 hours** — about 2.9 years of continuous spinning, spread over
  12 years. *(§10.7)*
- **The arm is worn out.** To save power the disk keeps parking that arm and pulling it back. It has
  done this **599,407 times against a design rating of 600,000** — so it has used up **99.9% of the
  movement it was built for**. Each park/unpark also freezes the PC for a moment while the arm
  reloads. *(§10.8)*
- **An important distinction:** the *surface* your data sits on is perfectly clean — zero bad
  sectors. It is the *moving parts* that are worn. So your data is safe right now, but the mechanism
  that reaches it is at the end of its life. *(§10.8)*

### Second cause: not enough memory (RAM)

- You have **8 GB**, and at one point only **0.34 GB was free**.
- When RAM fills up, Windows dumps the overflow onto the hard disk to make room — and the hard disk
  is problem #1. **The two problems make each other worse.** *(§2.4)*
- This is why the PC gets progressively worse the longer it stays on and the more tabs you open.

### Third cause: a failing SD card — this is what caused the sudden *freezes*

- The SD card reader threw **21 read errors**, then physically disconnected itself from the system
  mid-investigation. It died that day. *(§2.3, §10.7)*
- When storage fails, Windows doesn't give up immediately — it retries, and everything waits. That
  is a total freeze, not just slowness.
- **Slowness and freezing are two different problems.** The disk explains slow. The SD card
  explained the freezes.

### Fourth: the PC is probably overheating

- It has shut off instantly, without warning, **30 times** in the last four months. *(§10.6)*
- The battery is fine and no hardware faults were logged — which usually means heat. And the hard
  disk's own log confirms it **has overheated in the past**. *(§10.8)*
- After 12 years the fan is almost certainly clogged with dust and the thermal paste on the
  processor has dried out. *(§7.4)*

### Fifth: the disk is being shaken while it works

- It has detected **8,319 physical shocks** — the laptop being moved, bumped or carried while the
  platters are spinning. *(§10.8)*
- Each one can force an emergency arm-park, which stalls the PC and wears the mechanism out faster.

### And one thing that is *not* the problem

- You suspected **"system interrupts." Ruled out.** Those readings were 0.15% — completely idle.
  Nothing wrong there. *(§2.1)*
- **Fragmentation is fine too** (1.03 — essentially perfect). The usual "defrag your PC" advice will
  not help you. *(§10.3)*

### What to actually do

| Priority | Action | Why |
|---|---|---|
| **1. This week** | **Back up your files** to an external drive | The disk mechanism is at 99.9% of its life. Your data is readable *today* — that may not stay true, and worn disks give no warning. |
| **2. This week** | **Buy a 1 TB SATA SSD** (₹3,500–6,500) | Fixes the biggest slowness cause *and* replaces the worn-out disk. One purchase solves two problems. *(§7.1)* |
| **3. Now, free** | **Stop using the SD card slot** | Stops the freezes immediately. *(§7.3)* |
| **4. Now, free** | **Keep the laptop flat; don't move it while it's on** | Stops adding wear until the SSD arrives. |
| **5. With the SSD** | **Clean the fan and repaste the CPU** | The same panel comes off, so it is free effort. Likely fixes the random shutdowns. *(§7.4)* |
| **6. Optional** | **RAM 8 GB → 16 GB** (₹2,500–4,000) | Fixes cause #2. Do the SSD first if you can only afford one. *(§7.2)* |

**The short version:** your PC is slow because of a 12-year-old mechanical hard disk that is now also
**worn out and close to failing**. Back up your files, then replace it with an SSD. That single
change fixes the slowness and removes the risk at the same time.

*Full step-by-step ordering, including the software cleanup already done, is in §11.*

---

## 0. Executive summary

You suspected **disk errors** or **system interrupts**. Here is the verdict on both, plus what
actually turned out to be wrong.

| Your hypothesis | Verdict | Evidence |
| --- | --- | --- |
| System interrupts / DPC storms | **Ruled out** | `% Interrupt Time` 0.15% avg, 0.39% peak. `% DPC Time` 0.12%. These are idle-machine numbers. |
| Large disk errors | **Real — but on the wrong disk** | All 21 "bad block" errors were on the **SD card reader** (Disk 1), not the main drive. The main HGST logged **zero** device errors in 60 days, and the SD reader has since vanished from `Get-PhysicalDisk` entirely (§10.7). |
| The main drive is dying | **Not of bad sectors — but it is mechanically worn out** | Full SMART attribute table read 2026-08-05 (§10.7): reallocated, pending, uncorrectable, spin-retry and end-to-end error counts are **all zero** after 25 005 power-on hours — the *media* is sound. But attribute 193 shows **599,407 head load/unload cycles against a ~600,000 rating: 99.9% of rated mechanical life** (§10.8). Sound platters on a worn actuator. |

**The real ranking of causes, biggest first:**

1. **The 5400 RPM mechanical hard disk.** ~10 ms average read latency, 20 ms peaks, 66 MB/s
   sequential, ~537 small-file writes/sec. This is a uniform tax on literally everything the
   machine does. It is the single dominant cause.
2. **RAM exhaustion.** 8 GB installed, and at the time of writing **0.34 GB free** with a 17-day
   uptime. When RAM runs out Windows pages to disk — and the disk is cause #1. The two multiply
   each other.
3. **A dying SD card.** It threw 21 bad-block errors and then **physically dropped off the bus
   mid-investigation**. Storage driver retries block the calling thread, which is what produced
   your *sudden freezes* as opposed to uniform slowness.

**The single highest-value fix is an SSD.** Nothing else is close — and as of the second elevated
run it is also the **most urgent** fix, because the drive it replaces is at 99.9% of its rated
head-park life (§10.8).

> **Update (2026-08-05, elevated follow-up — see §10):** the blocked admin-only checks have since
> been run. They **confirm the ranking above** and add three things: the HGST has **zero read errors
> in 25,005 power-on hours** and is not degrading (it is slow, not sick); a **22.5-second maximum
> read latency** was recorded, which is the measured fingerprint of the freezes in cause #3; and
> **file fragmentation is a non-issue (1.02 fragments/file)** while **free space is shattered into
> 31,457 fragments**, which is a hard argument against running the staged Windows upgrade on this
> volume (§4).
>
> **Update 2 (2026-08-05, second elevated run — see §10.8):** the SMART decoder was extended to
> understand *mechanical wear* as distinct from *media faults*, and the picture changed. The drive
> is at **99.9% of its rated head-park life**, has recorded **8,319 physical shock events**, and has
> **overheated in the past** (attribute 190's worst-ever value went past its own threshold and
> recovered) — which is independent corroboration for the thermal-trip theory behind the 30
> unexplained power losses in §10.6. Free-space fragmentation has also worsened from 31,457 to
> **46,302 fragments**.

---

## 1. Confirmed hardware inventory

| Component | Detail |
| --- | --- |
| Model | HP Notebook, Hewlett-Packard board `80C3` rev `96.02` |
| BIOS | Insyde `F.02`, dated **2015-03-24** |
| Firmware mode | **Legacy BIOS** (not UEFI) |
| CPU | Intel Core **i3-4005U** @ 1.70 GHz — Haswell ULV, 2 cores / 4 threads, no turbo |
| RAM | **2 × 4 GB** Samsung DDR3-1600 SO-DIMM (`M471B5173BH0-YK0`, `M471B5173DB0-YK0`) — **both slots full** |
| RAM ceiling | 2 slots, SMBIOS max **16 GB** |
| Storage | **HGST HTS541010A9E680**, 932 GB, 2.5" 7 mm SATA, **5400 RPM**, firmware `JA0OA7G0` |
| Controller | Intel 8 Series Chipset SATA **AHCI** (SATA III, 6 Gb/s) |
| Partition style | **MBR**, one extended partition |
| OS | Windows 10 Pro **1909**, build **18363** (64-bit) |

**Partition layout (Disk 0, MBR):**

| Part | Letter | Label | Size | Free | Free % |
| --- | --- | --- | --- | --- | --- |
| 1 | C: | — | 141.2 GB | 33.4 GB | 23.6% *(after §3.1)* |
| 3 | D: | DATA | 561.8 GB | 190.0 GB | 33.8% |
| 2 | E: | — | 198.8 GB | 17.7 GB | **8.9%** |

Two facts here matter later: the controller is **SATA III**, so an SSD will run at full speed; and
the disk is **MBR + Legacy boot**, which changes how you migrate to that SSD (see §7).

---

## 2. What I measured, and what it showed

### 2.1 Interrupts and DPCs — clean

```
% Interrupt Time   0.15% avg   0.39% max
% DPC Time         0.12% avg
Processor Frequency  1700 MHz  @  % Processor Performance 99.7
```

I initially flagged 88 `Kernel-Processor-Power` event-55 entries as possible thermal/power
throttling. On inspection they are **benign boot-time capability dumps**, not throttle events — and
the live counters confirm it: the CPU is running at its full 1700 MHz rated clock at 99.7%
performance. There is no throttling and no interrupt storm.

**Your interrupt hypothesis is refuted.** This is worth knowing because chasing driver/interrupt
problems on this machine would have been wasted effort.

### 2.2 Disk latency and throughput — this is the bottleneck

```
Avg. Disk sec/Transfer   ~10 ms average,  ~20 ms peak
Avg. Disk Queue Length   elevated under normal desktop load
Sequential write 256 MB  3857 ms  ->   66.4 MB/s
Small-file write 300x4K   558 ms  ->  537 files/s
```

For calibration: a modern SATA SSD does **~0.1 ms** per transfer, ~500 MB/s sequential, and tens of
thousands of small writes per second. Your drive is **~100× slower on latency** and roughly **8×
slower on sequential throughput**.

Latency is what you *feel*. Every application launch, every file open, every Windows Update check,
every Chrome tab restore is a burst of small random reads, and each one costs ~10 ms of pure
mechanical seek time. That is the uniform "everything is sluggish" sensation.

### 2.3 Disk errors — real, but not where you thought

21 × Event ID **7** from provider `disk` ("The device has a bad block"). Grouping them by the
`\Device\HarddiskN\DRn` field in the message showed **every single one** was `Harddisk1` — the
**Generic SD/MMC card reader** (drive G:), not the HGST system drive.

Then, between my first and second scan, something notable happened:

- Last bad block: **2026-08-05 15:43**
- Shortly after: **Disk 1 disappeared from `Get-Disk` entirely.**
- Current state: only Disk 0 is attached.

That card is not degrading, it has **failed**. Anything on it should be treated as lost unless it
reads back cleanly elsewhere.

**Why this mattered for perceived speed:** when a storage device throws I/O errors, the driver
retries with timeouts before giving up. The thread that issued the read blocks for the whole retry
window. Explorer enumerating drives, a file dialog opening, an app scanning removable media — any
of these would hang for seconds. This is almost certainly the source of your *intermittent freezes*,
which is a different symptom from the constant HDD-induced sluggishness.

### 2.4 Memory pressure — worse than it first appeared

| Measurement | First scan | Latest scan |
| --- | --- | --- |
| Free physical RAM | ~2.0 GB | **0.34 GB** |
| Commit charge | 6.72 / 15.93 GB | — |
| Uptime | — | **17 days** (last boot 2026-07-19) |

Top consumers observed: Chrome (9 processes), VS Code (7 processes), and the Claude CLI — roughly
3.5 GB between them.

With 348 MB free, Windows is continuously trimming working sets and paging to `pagefile.sys` —
which lives on the 5400 RPM disk. **Cause #2 feeds directly into cause #1.** This is why the machine
feels progressively worse the longer it stays up, and why a reboot temporarily helps.

A 17-day uptime on an 8 GB machine running Chrome and VS Code is itself part of the problem.

### 2.5 Other findings

| Finding | Severity | Note |
| --- | --- | --- |
| Windows 10 **1909**, build 18363 | **High** | Feature-update support ended **May 2021**. Windows 10 as a whole reached end of support **October 2025**. You are running an unsupported OS on an unsupported branch — no security patches. |
| ~~7 ×~~ **35 × `Kernel-Power` event 41** | **High** | **Corrected — see §10.6.** The 60-day window used here understated it: there were **35 unexpected shutdowns between 2026-04-14 and 2026-07-17**, of which 5 were hangs you force-killed. Battery is ruled out (§10.5); silicon is clean (no WHEA). None since 2026-07-17. |
| E: at **8.9%** free | Medium | NTFS allocation quality degrades badly below ~10-15% free. Confirmed on C: — see §10.3, where free space is fragmented into 31,457 pieces. E: is fuller still. |
| `WSearch` (Windows Search indexing) | Medium | Indexing does exactly the random small I/O this disk is worst at. **You have already stopped and disabled it** — confirmed. |
| `C:\$Windows.~BT` (1.26 GB) | **Do not delete** | See §4 — this is a **staged, pending Windows feature upgrade**, not junk. |
| Fast Startup / hibernation | Informational | See §5 — you turned this off; there's a tradeoff worth understanding. |

---

## 3. What has already been changed

You applied some fixes yourself between my scans. Verified current state:

- ✅ `hiberfil.sys` — **gone** (3.17 GB reclaimed)
- ✅ `WSearch` — **Stopped and Disabled**
- ✅ `Windows.edb` — **deleted** (§3.1 — the single largest reclaim on this machine)
- ✅ C: free space — **20.3 GB → 33.4 GB** (14.4% → **23.6%**)

The cleanup script correctly detects and skips all of these, so re-running it is safe and idempotent.

### 3.1 The 15.1 GB left behind by disabling search — **done, 2026-08-05**

Disabling `WSearch` stopped the indexing *load*, but it did **not** remove the index *file*. The
elevated `-Apply` run on 2026-08-05 reported:

```
   Current: Status=Stopped  StartType=Disabled
   Index database:    15.10 GB  (C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb)
```

**15.1 GB of pure dead weight on a 141 GB drive with 23.1 GB free.** Nothing reads it while the
service is disabled, and Windows regenerates it from scratch if search is ever re-enabled.
Reclaiming it takes C: from 16.4% free to roughly **27% free** — more than the hibernation file,
the upgrade staging and every temp cache in this report **combined**, by an order of magnitude.

This is now automated as §4b.3 of the script (elevated + `-Apply -Aggressive`, with a prompt), or
you can do it by hand:

```powershell
# Elevated. Safe ONLY because WSearch is already Disabled.
Remove-Item 'C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb' -Force
```

The one trade-off: if you later decide you want Start-menu file search back, re-enabling `WSearch`
triggers a full re-crawl — hours of background seek load on this 5400 RPM disk. That argues for
re-enabling it *after* the SSD swap, not before.

**Outcome.** The file is gone. The next run of the script reports `Index database: not found.` and
§4b.3 reports `Not present -- nothing to reclaim.` C: free space measured across the two runs:

| | Free | % free |
| --- | --- | --- |
| Before | 23.10 GB | 16.4% |
| After | **33.40 GB** | **23.6%** |
| Net gain | **+10.30 GB** | +7.2 pts |

Note the net gain is 10.3 GB, not the full 15.1 GB the file occupied — roughly 4.8 GB was written
elsewhere on C: between the two runs (ordinary system and application activity over a working day).
The reclaim itself was complete; it was simply partly re-consumed. This is the largest single space
recovery in the whole investigation, and it cost nothing.

---

## 4. `C:\$Windows.~BT` — read this before deleting it

Every "free up space" guide on the internet will tell you this folder is leftover junk. **On your
machine right now, it is not.**

I inspected the contents:

| Subfolder | Date |
| --- | --- |
| `NewOS`, `Store`, `Work`, `Sources` | **2026-08-03** |
| `boot`, `efi`, `support`, `setup.exe` | 2019 |

Fresh `NewOS` and `Sources` trees dated three days ago mean **Windows Update has staged a feature
upgrade and is waiting to install it.** Deleting the folder cancels that upgrade and forces the
entire multi-gigabyte download to start over.

**Recommendation: leave it alone, and do the SSD swap first.** A Windows feature upgrade wants
~20 GB of working space. C: has 33.4 GB free after §3.1 — better, but still on a 12-year-old drive, and a failed upgrade
mid-flight on a nearly-full volume is a genuinely bad day. Install the SSD, then let the upgrade run
onto the fresh, fast, roomy drive.

The `-Aggressive` mode of the cleanup script will *warn you in red* if it detects a staged upgrade
newer than 30 days, and it drives the supported `cleanmgr` handlers rather than force-deleting the
TrustedInstaller-owned tree. It will **never** run `takeown` + `rmdir` on this folder — that desyncs
Windows Update's servicing state and is much harder to repair than it is to cause.

### 4.1 Disk Cleanup was tried, and declined

On 2026-08-05 the `-Aggressive` prompt was accepted and `cleanmgr /sagerun` ran to completion:

```
   cleanmgr exited with code 0.
   [DONE]    Partially cleared;     1.26 GB still present.
   Disk Cleanup would not release these:
     C:\$Windows.~BT
```

**Exit code 0 with the folder untouched is not a script failure — it is Disk Cleanup agreeing with
§4.** The handler recognises the tree as a live, pending upgrade and declines to remove it. Windows
is protecting its own servicing state, and the script correctly reports the discrepancy instead of
claiming a reclaim it did not get, and correctly refuses to escalate to `takeown`.

The practical upshot: **this 1.26 GB is not available to you** while the upgrade is staged. Either
let the upgrade install (recommended — after the SSD swap) or cancel it deliberately through
*Settings → System → Storage → Temporary files*. Do not go looking for a way to force it.

---

## 5. The hibernation trade-off (a correction to my earlier advice)

I initially told you to run `powercfg /hibernate off`. **That advice was incomplete and I corrected
it**, but you had already applied the original version. Here is the full picture.

**Fast Startup is built on top of hibernation.** It works by hibernating the *kernel session* (not
your apps) at shutdown and restoring it at boot. `powercfg /hibernate off` deletes `hiberfil.sys`
and therefore **silently kills Fast Startup too**.

Your current state (`powercfg /a`): Hibernate, Hybrid Sleep, **and Fast Startup all unavailable**.

| Option | Disk cost | Effect |
| --- | --- | --- |
| Hibernation fully off *(your current state)* | 0 GB | Coldest, slowest boots. On a 5400 RPM disk this hurts noticeably. |
| `powercfg /hibernate /type reduced` | ~1.6 GB | **Keeps Fast Startup**, drops full hibernate-to-disk. Best balance on an HDD. |
| Hibernation fully on | ~3.2 GB | Everything available. |

**My recommendation: restore reduced mode** — you buy back meaningfully faster boots for 1.6 GB on a
141 GB volume, and boot time is exactly where a slow disk hurts most:

```powershell
# Run as Administrator
powercfg /hibernate on
powercfg /hibernate /type reduced
powercfg /a          # verify Fast Startup is back
```

Keeping it off is a perfectly legitimate choice if you value the 1.6 GB more — it's your call, not a
mistake. The script defaults to `Reduced` (`-HibernateMode Reduced`) and will never turn hibernation
off unless you explicitly pass `-HibernateMode Off`.

---

## 6. Recommendations, ranked by value per rupee

| # | Action | Cost | Impact | Effort | Risk |
| --- | --- | --- | --- | --- | --- |
| 1 | **Replace HDD with a SATA SSD — now urgent, not optional** | ₹3,500–6,500 | ★★★★★ | Medium | Low |
| 2 | **Stop using the SD card; replace it** | ₹500–1,500 | ★★★★☆ (freezes) | Trivial | None |
| 3 | **RAM 8 GB → 16 GB** | ₹2,500–4,000 | ★★★☆☆ | Low | Low |
| 4 | Reboot weekly; cap Chrome/VS Code | Free | ★★★☆☆ | Trivial | None |
| 5 | Restore Fast Startup (§5) | Free | ★★☆☆☆ | Trivial | None |
| 6 | Run `pc-cleanup.ps1` periodically | Free | ★★☆☆☆ | Trivial | Low |
| 7 | Free up E: to >15% | Free | ★☆☆☆☆ | Low | None |
| 8 | Address the OS support situation (§8) | Varies | Security | High | Medium |

**Trade-off notes:**

- **#1 has changed character (2026-08-05, §10.8).** It was the biggest *speed* win. SMART attribute
  193 now reads **599,407 head load/unload cycles against a ~600,000 rating — 99.9% of the drive's
  rated mechanical life**. That reclassifies the SSD from an upgrade you schedule to a replacement
  you do before the drive stops. The media is still clean, which is exactly the profile that goes
  from "healthy" to "will not spin up" with no warning — and it is also why a clone will still read
  cleanly *today*. Do it while that is still true.
- **SSD before RAM, always.** More RAM reduces *how often* you page; an SSD makes paging ~100×
  cheaper *and* speeds up everything else. If you can only afford one, buy the SSD.
- **Do both if you can.** They compound: on a 2-core i3 with 16 GB and an SSD, this machine becomes
  genuinely pleasant for browsing, editing and light dev work. It will still be slow at
  compilation, video encoding, and anything CPU-bound — the i3-4005U is a 15 W dual-core with **no
  turbo boost**, and no storage or memory upgrade changes that.
- **Don't upgrade the CPU.** It is soldered (BGA). Not an option.
- **Know when to stop.** Total upgrade cost lands around ₹6,000–10,500. That's good value for
  extending a working laptop by 2–3 years, but be clear-eyed: you are investing in a machine whose
  CPU is a 2014 dual-core and whose BIOS was last updated in 2015. If your workload is heavy
  development, put the money toward a new machine instead.

---

## 7. Hardware upgrade guide

### 7.1 SSD replacement — the main event

**What to buy:** a **2.5-inch, 7 mm, SATA III** SSD. Not M.2, not NVMe — this machine has no M.2
slot, only a single 2.5" SATA bay.

| Capacity | Fits your data? | Notes |
| --- | --- | --- |
| 500 GB | Tight | Current usage: C: 118 GB + D: 372 GB + E: 181 GB ≈ **671 GB**. You'd have to prune. |
| **1 TB** | **Yes — recommended** | Straight like-for-like swap, no data triage needed. |

Good options in India: Crucial MX500 1TB, Samsung 870 EVO 1TB, WD Blue SA510 1TB, Kingston KC600 1TB.
Any mainstream 1 TB SATA SSD with **DRAM cache** is fine; avoid the cheapest no-name DRAM-less
drives — their sustained-write performance collapses, which partly defeats the point.

**What else you need:**
- A **USB-to-SATA 2.5" adapter or enclosure** (~₹400–800) to connect the SSD during cloning.
- A small Phillips screwdriver.

**Critical detail for your machine — MBR + Legacy BIOS:**

Your disk is **MBR** and your firmware boots in **Legacy** mode. This is actually the *easy* case
for cloning: a sector-level MBR-to-MBR clone boots without any firmware reconfiguration. Just do
**not** let cloning software "helpfully" convert the target to GPT — a GPT disk will not boot on a
Legacy-BIOS-only machine, and you will get a black screen with a blinking cursor.

**Procedure (clone — recommended):**

1. **Back up anything irreplaceable first.** Cloning is safe in practice, but the source drive is 12
   years old and you get one attempt at this.
2. Run `pc-cleanup.ps1 -Apply` first — a smaller source clones faster.
3. Connect the SSD via the USB-SATA adapter.
4. Clone with **Macrium Reflect Free**, **Clonezilla**, or the vendor's tool (Samsung Data
   Migration / Acronis True Image for Crucial/WD — free with those brands).
   - Clone **all partitions** including the hidden system-reserved one if present.
   - Keep the target as **MBR**.
   - Let it resize partitions to fill 1 TB, or clone 1:1 and expand later in Disk Management.
5. Power off. Remove the battery and AC. Open the bottom service panel, unscrew the drive caddy,
   slide the HGST out, put the SSD in the same caddy, reassemble.
6. Boot. If it doesn't, enter BIOS (usually **Esc** then **F10** on HP) and confirm boot order and
   that **AHCI** is still set (it is — verified as AHCI already; do not switch it to IDE).
7. Keep the old HGST in the USB enclosure as a full backup for a few weeks before reusing it.

**Alternative — clean install:** faster and cleaner in the long run (12 years of accumulated cruft
is real), but read §8 first, because "which Windows do I install" is genuinely complicated on this
machine.

**After the swap:**
```powershell
# Verify Windows sees an SSD and enabled TRIM automatically
Get-PhysicalDisk | Select-Object FriendlyName, MediaType   # should say SSD
fsutil behavior query DisableDeleteNotify                   # 0 = TRIM enabled
```
Do **not** defragment an SSD. Windows handles SSDs correctly on its own (it runs TRIM/retrim instead
of defrag) as long as it correctly detects `MediaType = SSD`.

### 7.2 RAM upgrade — 8 GB → 16 GB

- **Ceiling:** 2 slots, SMBIOS reports **16 GB max**. Both slots are currently occupied by 4 GB
  modules, so this is a **replacement, not an addition** — you must remove both 4 GB sticks.
- **What to buy:** **2 × 8 GB DDR3L-1600 SO-DIMM (PC3L-12800), 204-pin, 1.35 V.**
  - Buy **DDR3L** (low voltage), not plain DDR3. Haswell ULV mobile chipsets expect 1.35 V.
    DDR3L modules are dual-voltage and safe; plain 1.5 V DDR3 may not train reliably.
  - Buy a **matched pair** to keep dual-channel mode. Your current sticks are already a
    dual-channel pair — losing that costs real bandwidth on integrated graphics.
- **Slots:** `Bottom - Slot 1 (left)` / `Bottom - Slot 2 (right)`, both under the bottom service panel.
- **Procedure:** power off, unplug, **remove the battery**, ground yourself, press the retaining
  clips outward, each module pops up at ~30°, pull it out, insert the new one at the same angle and
  press down until the clips latch. Reassemble, boot, verify:
  ```powershell
  Get-CimInstance Win32_PhysicalMemory | Select-Object DeviceLocator, @{n='GB';e={$_.Capacity/1GB}}, Speed
  ```
- **If it doesn't POST:** reseat both. If it still fails, test one stick at a time in slot 1 to
  identify a bad module.

### 7.3 The SD card

Stop using it. It threw 21 bad-block errors and then dropped off the bus entirely — that is a
hardware failure, not a driver glitch. If it has data you need, image it with `ddrescue` on another
machine rather than copying files normally; a normal copy will stall on every bad sector and may
finish the job of killing it.

Also verify the failure is the *card* and not the *reader*: try a different, known-good card in the
same slot. If that one also errors, the reader is at fault — in which case just avoid the slot and
use a USB card reader (~₹200).

### 7.4 Also worth doing while the machine is open

- **Clean the fan and heatsink — now RECOMMENDED, not optional.** §10.6 found **35** unexpected
  shutdowns with no BSOD, no crash dump and **no WHEA hardware errors**, on a machine whose battery
  is healthy and on AC. That combination points at a **board-level thermal trip**, and 12 years of
  dust is the obvious cause.
- **Repaste the CPU** while you have it open — 12-year-old thermal paste is long dead. On this
  chassis the heatsink is under the same bottom panel as the drive and RAM, so it costs no extra
  disassembly during the SSD swap.
- ~~Check the battery~~ — **done. 77.1% health, functional, ruled out as a cause (§10.5).**

---

## 8. The Windows situation (read before a clean install)

This is the genuinely awkward part, and there's no clean answer.

- You're on **Windows 10 1909**, whose branch lost support in **May 2021**.
- **Windows 10 as a whole** reached end of support in **October 2025**. It is now August 2026 — you
  are ~10 months past end-of-life for the entire product, receiving no security updates.
- **Windows 11 does not officially support your CPU.** The i3-4005U (Haswell, 2014) is far below
  the 8th-gen-Intel floor, and the machine has **no TPM 2.0 and boots Legacy/MBR** — it fails the
  requirements on three independent counts.

Your realistic options:

| Option | Pros | Cons |
| --- | --- | --- |
| **Let the staged upgrade install (§4)** | Gets you to a much later Win10 build; zero effort | Still an EOL OS; no security patches after install |
| **Windows 10 ESU (consumer)** | Officially supported security updates | Paid, time-limited, and you must first be on 22H2 |
| **Windows 11 via Rufus/registry bypass** | Modern, currently patched | Unsupported config; updates can break; needs GPT+UEFI conversion (`mbr2gpt`) — extra risk on a Legacy-only BIOS that may not have a UEFI mode at all |
| **Linux (Mint / Xubuntu / Fedora)** | Fully supported, patched, and *dramatically* faster on 2C/8GB hardware | Relearning; Windows-only apps need Wine/VM or don't run |

**My recommendation, in order:**

1. **Do the SSD swap first**, keeping your current install via clone. Get the speed win with zero
   compatibility risk.
2. **Then let the staged feature upgrade run** onto the fast, roomy drive — that gets you to a
   modern Win10 build safely.
3. **Then decide on the long-term OS question** with a working, fast machine and no time pressure.
   If this laptop is a secondary/browsing machine, **Linux Mint on that SSD would make it feel new**
   and solves the security problem outright. If you need Windows-specific software, look at ESU.

Do not attempt `mbr2gpt` + UEFI conversion + Windows 11 on the current failing-era HDD. Too many
irreversible steps stacked on aging hardware.

---

## 9. How to run `pc-cleanup.ps1`

Located alongside this report:
`E:\Downloads\AI Codes\openalgo\strategies\SS_Projects\others\PC_Slow\pc-cleanup.ps1`

### 9.1 Safety model

- **Report-only by default.** Without `-Apply` it changes nothing at all. Run it that way first.
- **Never touches user data.** No Documents, Desktop, Downloads, Pictures, or project folders.
- **Never empties the Recycle Bin.** It reports the size and lets you decide.
- **Aggressive steps are opt-in, gated, and confirmed.** They require `-Apply` **and**
  `-Aggressive` **and** an elevated session **and** an interactive `y/N` confirmation.
- **Fails closed.** In a non-interactive host where it cannot prompt, it *skips* the aggressive step
  rather than assuming yes. Pass `-Yes` to authorize explicitly.
- **Idempotent.** Re-running is safe; it detects already-applied changes and prints `[SKIP]`.

### 9.2 Parameters

**The script documents itself.** Rather than working from this table, run:

```powershell
pwsh -File .\pc-cleanup.ps1 --help
```

That prints a full guide — every argument with a paragraph of explanation, the safety
model, and worked examples — and exits without doing anything. All of these forms work:
`-Help` · `-h` · `--help` · `/?` · `-Usage` · `--usage` · bare `help`.

An argument that doesn't match anything is **rejected with exit code 2** rather than
silently ignored. That matters on a script that deletes files: a typo'd `-Aply` will not
quietly become a no-op flag on a run you meant to be destructive. Options must be **named** —
bare positional values are refused too, so `pc-cleanup.ps1 C` errors instead of being
mistaken for `-ScanDrives C`.

Summary table:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `-Apply` | *(off)* | Actually make changes. Without it, report only. |
| `-Aggressive` | *(off)* | Enable the larger reclaims (hibernation sizing, Disk Cleanup handlers, orphaned search index). Requires `-Apply` + admin. |
| `-Yes` | *(off)* | Auto-confirm aggressive prompts. Use only when you know what you're authorizing. |
| `-HibernateMode` | `Reduced` | `Reduced` (keeps Fast Startup) · `Off` (kills it) · `None` (don't touch hibernation). |
| `-ScanDrives` | `C`, `E` | Drives to scan for large files/folders. |
| `-TopN` | `20` | How many large items to list. |
| `-TempOlderThanDays` | `7` | Only delete temp files older than this. |
| `-SkipLargeFileScan` | *(off)* | Skip the slow disk-walk (it is slow on your HDD). |
| `-Diagnostics` | *(off)* | Run the read-only health panel (§6) after the cleanup passes. Unaffected by `-Apply` — it never changes anything. |
| `-DiagnosticsOnly` | *(off)* | Run **only** the health panel and exit. Implies `-Diagnostics`, forces `-Apply` off. This is the periodic-checkup mode. |
| `-EventDays` | `120` | Lookback window for §6.5 shutdown/hardware events. Deliberately wide: the original 60-day pass **undercounted the shutdowns 5×** (see §10.6). |
| `-DiagnosticsOutDir` | *(script folder)* | Where the generated `battery-report.html` is written. `powercfg`'s own default dumps it into System32. |
| `-Help` / `-Usage` | *(off)* | Print the full built-in usage guide and exit. Also accepts `-h`, `--help`, `--usage`, `/?`, bare `help`. |

### 9.3 Usage

```powershell
cd "E:\Downloads\AI Codes\openalgo\strategies\SS_Projects\others\PC_Slow"

# 0. Full usage guide for every argument. Runs nothing.
pwsh -File .\pc-cleanup.ps1 --help

# 1. Look first — changes nothing.
pwsh -File .\pc-cleanup.ps1

# 2. Faster report, skipping the slow disk walk.
pwsh -File .\pc-cleanup.ps1 -SkipLargeFileScan

# 3. Apply the safe cleanup (temp files, caches, service tuning).
pwsh -File .\pc-cleanup.ps1 -Apply

# 4. Aggressive reclaims — run this one from an ELEVATED terminal.
pwsh -File .\pc-cleanup.ps1 -Apply -Aggressive

# 5. Aggressive, unattended, keeping Fast Startup.
pwsh -File .\pc-cleanup.ps1 -Apply -Aggressive -Yes -HibernateMode Reduced

# 6. Health panel only — no cleanup. Run this ELEVATED for the full picture.
pwsh -File .\pc-cleanup.ps1 -DiagnosticsOnly

# 7. Cleanup plus health panel, looking back a full year for shutdown events.
pwsh -File .\pc-cleanup.ps1 -Apply -Diagnostics -EventDays 365
```

**Run #6 elevated.** Un-elevated it still gives you battery health, the shutdown/WHEA
forensics and the power state, but reliability counters, SMART, the dirty flag,
fragmentation and thermal zones all report "needs Administrator" and are skipped.

If PowerShell 7 (`pwsh`) isn't installed, substitute `powershell -ExecutionPolicy Bypass -File ...`.

To elevate: right-click PowerShell → *Run as administrator*, then `cd` to the folder.

### 9.4 What each section does

| Section | Action | Needs admin? |
| --- | --- | --- |
| §1 Removable media & bad blocks | **Report only.** Maps `disk` event-7 errors to physical disks and says whether each is still attached. | Read-only |
| §2 Windows Search | Stops and disables `WSearch` (already done on your machine). | Yes |
| §3 Temp & caches | Deletes user/system temp, Windows Update download cache, thumbnail/font/icon caches, browser caches — all older than `-TempOlderThanDays`. | Partly |
| §4 Recycle Bin | **Report only.** Prints size; never empties. | No |
| §4b.1 Hibernation *(aggressive)* | Sets hibernation per `-HibernateMode`. | Yes |
| §4b.2 Disk Cleanup handlers *(aggressive)* | Drives `cleanmgr /sagerun` for Previous Installations, Setup Logs, Update Cleanup, Temporary Setup Files. **Warns in red if a staged upgrade is detected** (§4). Removes its own `StateFlags` afterward so your manual `cleanmgr` runs aren't polluted. Prints the manual route for survivors and explicitly refuses `takeown`/`rmdir`. | Yes |
| §4b.3 Orphaned search index *(aggressive)* | Deletes `Windows.edb` — **but only when `WSearch` is already `Disabled`**, in which case nothing reads the file. If the service is still enabled it refuses and explains why (Windows would just rebuild it). On your machine this was **15.1 GB**, the single largest reclaim available — **taken 2026-08-05**, so it now reports "not present". | Yes |
| §5 Large files & folders | **Report only.** Top-N largest items on `-ScanDrives`. Slow on an HDD. | Read-only |
| §6 Diagnostics *(`-Diagnostics`)* | **Report only, always.** The scripted form of every manual check from this investigation — see the breakdown below. | Partly |

Section 6 replaces the ad-hoc terminal commands used during the investigation, so the
whole panel is one command instead of a dozen pasted snippets:

| Sub-section | What it runs | Maps to |
| --- | --- | --- |
| 6.1 Reliability counters | `Get-StorageReliabilityCounter` — power-on hours, read/write error counts, start-stop and load-unload cycles, and the latency maxima decoded from ms into seconds | §10.1, §10.2 |
| 6.2 SMART | `MSStorageDriver_FailurePredictStatus` for the predict-fail bit, **plus a full decode of the 512-byte attribute table** from `MSStorageDriver_FailurePredictData` (+ thresholds): ID, current, worst, threshold and the 6-byte little-endian raw for all 30 records. Warns on any non-zero raw where zero is the only healthy value, and on any normalised value at/below threshold. Detects vendor-packed raw fields and refuses to grade them either way. **Also grades mechanical wear** — cycle counters carry a `WearLimit` rating and render as `% of rated life`, with ≥90% graded `[BAD ]`; **flags past recovered threshold breaches** (`Wst <= Thr` while `Cur` is healthy — the only trace an excursion leaves); **narrates G-sense shock events**; and **cross-checks its own load/unload count against 6.1's driver figure**, which disagree by 62× on this machine. Falls back to recommending CrystalDiskInfo when the driver exposes nothing | §10.7, §10.8 |
| 6.3 Filesystem | `fsutil dirty query` plus `defrag /A /V`, parsing **file** fragmentation and **free-space** fragmentation separately, and flagging the "big install has nowhere to land" case | §10.3 |
| 6.4 Battery | `Win32_Battery` plus a `powercfg /batteryreport` written to `-DiagnosticsOutDir` and parsed for design vs full-charge capacity → health % | §10.5 |
| 6.5 Shutdowns | Kernel-Power 41 over `-EventDays`, with the event XML decoded to split **hangs** (`PowerButtonTimestamp` ≠ 0) from **BSODs** (`BugcheckCode` ≠ 0) from **instant power loss**; plus WHEA-Logger, EventLog 6008 and crash-dump presence | §10.6 |
| 6.6 Thermals | `MSAcpi_ThermalZoneTemperature` with the tenths-of-Kelvin conversion; **skips unpopulated zones** (`CurrentTemperature = 0`, which decodes to −273.2 °C) instead of grading them healthy, and states that a cool ACPI zone is a board sensor and does not rule out a hot CPU core; falls back to HWiNFO64/Core Temp advice on firmware that publishes no zones | §10.7 |
| 6.7 Power state | `powercfg /a`, parsed by *section* so an unavailable state isn't misread as available, plus `hiberfil.sys` size | §5 |

Note that the whole `Thr` column, and therefore every threshold-based verdict in 6.2, **requires
Administrator** — the thresholds table is a separate WMI class with its own ACL. A non-elevated run
still decodes the attributes but cannot tell you whether any of them has crossed a limit.

Six notes on why the script differs from what you pasted into the terminal:

- Some of the commands I gave you used `Get-WmiObject`, which **was removed in PowerShell 7** —
  and your `PS System32>` window *is* PowerShell 7, which is why it errored with "the term
  `Get-WmiObject` is not recognized". The script uses `Get-CimInstance -Namespace root/wmi`,
  the supported replacement, which works in both PowerShell 7 and Windows PowerShell 5.1.
- A read-error field returning `$null` means *the driver doesn't report it* — the script
  says so rather than printing it as a reassuring `0`.
- A thermal zone reporting `0` decodes to **−273.2 °C**. That is not a cold sensor, it is an
  **absent** one, and the script labels it as such instead of passing it as healthy.
- A SMART raw value whose upper bytes are set is **vendor-packed data, not a count**. The script
  detects this and withholds a verdict rather than reporting HGST's attribute 187 as 2×10¹⁴ errors.
- Vendor packing has a **second form the upper-byte test misses**: attribute 192's raw is
  20,316,470 against a ~20,000 rating with the high bytes all zero. A cycle count more than 10× its
  rating is not a count either, so the script withholds a verdict there too rather than fabricating
  a 100,000%-worn alarm.
- **Two `LoadUnloadCycleCount` values exist and they are not the same number.**
  `Get-StorageReliabilityCounter` (6.1) reports what the storage driver has observed; SMART
  attribute 193 (6.2) reads the drive's own lifetime log. On this machine they read 9,583 and
  599,407. SMART is authoritative, and the script now says so in-panel whenever they diverge.

### 9.5 Expectations

The routine passes (§3 temp/caches) reclaim **almost nothing on your machine now** — the
2026-08-05 elevated run freed 0 KB, because previous runs already took it. Everything worth
having left is in §4b, and it is not "a few GB":

| Reclaim | Size | Gate | Status |
| --- | --- | --- | --- |
| **`Windows.edb` orphaned search index** | **15.10 GB** | `-Aggressive`, §3.1 | ✅ **taken 2026-08-05** |
| `C:\$Windows.~BT` upgrade staging | 1.26 GB | `-Aggressive` — **cancels the pending upgrade**, see §4 | Still present — Disk Cleanup declined it (§4) |
| Recycle Bin | 40.3 MB | Manual, never automatic | ✅ emptied |
| Temp & caches | ~250 KB | `-Apply` | Files in use; nothing left |

The index alone was worth more than everything else combined. **But do not expect any of it to fix
the slowness.** It cannot. The slowness is 5400 RPM mechanical latency plus RAM exhaustion, and only hardware fixes
those. The script's real value is (a) keeping the volumes healthy and (b) its report sections, which
tell you where the space actually went.

---

## 10. Elevated follow-up results *(added 2026-08-05, after the initial pass)*

The original investigation ran non-elevated, so several checks were blocked. They have since been
run with administrator rights. **Two conclusions below supersede what §2 and the old caveats said.**

### 10.1 Drive reliability counters — the HGST is not degrading

```
PowerOnHours            25005      ReadErrorsTotal          0
StartStopCycleCount      5829      ReadErrorsCorrected      0
LoadUnloadCycleCount     9583      ReadErrorsUncorrected    0
Wear                        0      WriteErrors*          (null)
Temperature / Max         0 / 0    ManufactureDate       (null)
```

| Counter | Reading |
| --- | --- |
| `PowerOnHours` 25,005 | ≈ **2.85 years of actual spinning**, not 12. The machine has spent most of its life powered off. Meaningful but not end-of-life; Backblaze-style failure curves climb sharply past ~35,000 h. |
| `ReadErrors*` all **0** | **No media degradation.** No corrected reads, no uncorrected reads, no retries. |
| `StartStopCycleCount` 5,829 | Well within the ~50,000 typical rating. |
| `LoadUnloadCycleCount` 9,583 | Well within the ~600,000 typical rating. |
| `Wear` 0 | SSD-only field. Meaningless here. |
| `Temperature` 0 / `TemperatureMax` 0 | **Not reported by this driver.** Not "0 °C" — thermals remain unmeasured. |
| `WriteErrors*` null | **Not reported.** Absence of evidence, not evidence of absence. |

Note the asymmetry: read-error fields return a real `0` while write-error fields return `null`. So
"zero read errors" is genuine positive evidence; nothing can be concluded about writes.

**This supersedes the earlier caution that the drive might be quietly failing.** It isn't. The disk
is *slow* (5400 RPM, ~10 ms latency) but it is not *sick*. The case for replacing it is entirely
about performance, not imminent data loss — though §11 step 1 still applies, because a 12-year-old
drive deserves a backup regardless of what its counters say.

### 10.2 Latency maxima — the freeze fingerprint

All three are in **milliseconds**:

```
ReadLatencyMax    22520   =  22.5 seconds
WriteLatencyMax   16757   =  16.8 seconds
FlushLatencyMax    7789   =   7.8 seconds
```

A single read that took **22.5 seconds** to complete. Spin-up from standby accounts for only 4–5 s,
so this is far beyond a parked-platter stall.

Critically, this sits alongside **zero read errors on this disk** — so the HGST's own media did not
cause it. The stall happened at the **storage stack** level. Two mechanisms explain it, and both are
already identified in §0:

1. **The failing SD card (§2.3).** The class driver retrying a dead device with timeouts blocks the
   port and the calling thread. This is the leading explanation.
2. **RAM exhaustion (§2.4).** Paging storms drive queue depth far beyond what a 5400 RPM disk can
   service, and queueing time is counted in these maxima.

These counters are the measured signature of your **freezes** — the intermittent multi-second hangs,
as distinct from the constant HDD sluggishness. They corroborate the §0 ranking; they don't change it.

### 10.3 Fragmentation — file fragmentation refuted, free-space fragmentation confirmed

`fsutil dirty query C:` → **NOT dirty.** Filesystem is consistent; no chkdsk pending.

```
Total fragmented space     = 5%          Fragmented files  = 2661
Average fragments per file = 1.02        Total fragments   = 11950
"You do not need to defragment this volume."
```

**File fragmentation is a non-issue.** At 1.02 average fragments per file, files are essentially
contiguous. **This corrects the earlier assumption that fragmentation was "probably significant" —
it is not, and defragmenting would be wasted wear on the drive.**

But the free-space half of the same report is a genuine finding:

```
Free space count        = 31457
Average free space size = 696.00 KB
Largest free space size = 608.10 MB
```

**Your ~20 GB of free space is shattered into 31,457 fragments averaging under 1 MB, and the largest
contiguous run is only 608 MB.** Your *files* aren't fragmented; your *free space* is. Every large
new write must be scattered across thousands of extents — thousands of mechanical seeks on a 5400 RPM
platter.

This is a hard, measured argument for **§4**: the staged ~20 GB Windows feature upgrade has **no
contiguous space to land in** on this volume. Do not run it here. Do it after the SSD swap.

```
MFT size          = 1.05 GB      MFT record count    = 1103359
MFT usage         = 100%         Total MFT fragments = 2
```

The MFT is only 2 fragments, so it is healthy *today* — but at **100% usage** it has outgrown its
reserved zone, so any further growth is allocated out of that same shattered free space. 1.1 million
files on a 141 GB volume is a lot; expect this to slowly worsen while the volume stays this full.

### 10.4 Space discrepancy — worth a look

`defrag` reported **20.34 GB** free on C:. The scan a few hours earlier read **23.50 GB**. That is a
**3.16 GB** gap, suspiciously close to `hiberfil.sys` at 3.17 GB.

- **If you ran `powercfg /hibernate on` (§5), this is fully expected and correct** — that's the file
  coming back, and it buys back Fast Startup.
- **If you didn't**, something else consumed 3 GB on C: today and is worth locating —
  `pc-cleanup.ps1` §5 (large files/folders) will find it.

### 10.5 Battery health — good, and it exonerates the battery

`powercfg /batteryreport` → `C:\Windows\System32\battery-report.html`:

| Field | Value |
| --- | --- |
| Battery | COMPAL `PABAS0241231`, Li-ion, 16.59 V design |
| Design capacity | **32,120 mWh** |
| Full charge capacity | **24,762 mWh** |
| **Health** | **77.1%** (22.9% degraded) |
| Runtime estimate | ~2 h (down from ~3.5 h when newer) |
| Current state | Present, `Status: OK`, on AC (`BatteryStatus 2`), 100% charged |

77% capacity after 12 years is good. Crucially, **the battery is present and functional**, which
means an AC-mains flicker **cannot** hard-kill this machine — the battery covers the gap. This
**rules the battery out** as the cause of the unexpected shutdowns below.

*(Capacity-history rows read `-` from 2026-07-29 onward simply because the machine has been on AC
continuously — no discharge cycles to record. Not a fault.)*

### 10.6 Unexpected shutdowns — 35, not 7, and two distinct failure modes

**This supersedes the §2.5 figure of "7 × Kernel-Power 41 in mid-July," which was measured over too
short a window and materially understated the problem.**

```
35 x Kernel-Power event 41 between 2026-04-14 and 2026-07-17
31 x EventLog 6008 (unclean shutdown) corroborating over 90 days
```

Decoded event data:

| Evidence | Reading |
| --- | --- |
| `BugcheckCode = 0` on **all 35** | **No BSOD.** Windows never reached the crash handler. |
| No `MEMORY.DMP`, no `C:\Windows\Minidump` entries | Consistent — nothing was ever written. |
| **WHEA-Logger: zero events in 120 days** | No CPU / RAM / cache / PCIe machine-check errors. **Silicon and memory are not faulting.** |
| `PowerButtonTimestamp ≠ 0` on **5 of 35** | Power button held down — the machine had **hung** and was force-killed. |
| Remaining **30** | Genuine instant power loss or total freeze, unlogged. |

**Two separate failure modes are mixed together:**

1. **At least 5 hard hangs.** These fit the storage evidence exactly — the 22.5 s max read latency
   (§10.2) plus the failing SD card (§2.3) retrying indefinitely. When the storage stack stalls
   forever the machine appears dead, the power button is the only recourse, and **no dump can be
   written because the disk that would receive it is the thing that is stuck.**
2. **30 instant deaths.** Not the battery (§10.5) and not faulting silicon (clean WHEA). The leading
   remaining suspect is a **thermal trip** — a board-level power cut leaves no time to log anything,
   which is the classic signature for a 12-year-old laptop with a dust-clogged heatsink and original
   thermal paste. **Unconfirmed — thermals are still unmeasured (§10.7).**

**The most important fact: it stopped.** Zero events since **2026-07-17**, with the last boot on
2026-07-19 — 17 clean days after three months of near-daily crashes. Something changed around then.
If that change is known (relocated the machine, removed a peripheral, stopped using the SD slot,
altered a power setting), it is likely the answer and the issue may already be resolved.

**Action:** do not chase this aggressively while it is quiescent, but (a) measure thermals under load,
and (b) treat the fan/heatsink clean + repaste in §7.4 as **raised from "worth doing" to
"recommended"**. Both candidate causes — storage stall and thermal trip — are addressed by work
already in the plan (SSD swap, abandon the SD card, clean the cooling system).

### 10.7 Still outstanding

> **All of the below are now automated.** Run `pwsh -File .\pc-cleanup.ps1 -DiagnosticsOnly`
> from an **elevated** terminal and section 6 performs every check on this list. The raw
> commands are kept here for reference. Note that `Get-WmiObject` **does not exist in your
> terminal** — the `PS System32>` window is PowerShell 7, which removed that cmdlet. Every
> snippet below therefore uses `Get-CimInstance -Namespace root/wmi`, which works in both
> PowerShell 7 and Windows PowerShell 5.1. The script itself uses `Get-CimInstance` throughout.

- **Thermals — now the single highest-value open question** (§10.6 hinges on it). The ACPI zones
  were read on 2026-08-05 and **did not settle it**:

  | Zone | Reading | Meaning |
  |---|---|---|
  | `ACPI\ThermalZone\TZ00_0` | −273.2 °C | **Not populated.** `CurrentTemperature = 0` decodes to absolute zero — it is the absence of a sensor, not a cold one. |
  | `ACPI\ThermalZone\TZ01_0` | −273.2 °C | Not populated. |
  | `ACPI\ThermalZone\TZ02_0` | 27.8 °C | A real reading — but a **chassis/board** sensor at idle, not the CPU core. |

  A 27.8 °C board sensor does **not** exonerate the CPU: cores routinely hit 100 °C while a sensor
  a few centimetres away still reads under 40 °C. **Still required: HWiNFO64 or Core Temp watching
  CPU *package* temperature under sustained load.** Sustained 90 °C+, or a spike toward 100 °C,
  confirms the thermal-trip theory for the 30 unexplained shutdowns — fix is the fan/heatsink clean
  and repaste in §7.4. *(Section 6.6 now labels unpopulated zones explicitly rather than grading
  −273.2 °C as "healthy", and states that zone ≠ core.)*
- ~~True SMART predict-fail has not been read~~ — **done, and it passes.**
  `MSStorageDriver_FailurePredictStatus` returns `PredictFailure: False`, `Reason: 0` for the HGST.
  Section 6.2 now goes further and decodes the full 512-byte **attribute table** from
  `MSStorageDriver_FailurePredictData`, because `PredictFailure` is a single bit that only trips
  once an attribute has *already* crossed its threshold. Results on 2026-08-05:

  | ID | Attribute | Cur | Wst | Raw | Verdict |
  |---|---|---|---|---|---|
  | 5 | Reallocated Sectors | 100 | 100 | **0** | Clean |
  | 196 | Reallocation Event Count | 100 | 100 | **0** | Clean |
  | 197 | Current Pending Sectors | 100 | 100 | **0** | Clean |
  | 198 | Offline Uncorrectable | 100 | 100 | **0** | Clean |
  | 10 | Spin Retry Count | 100 | 100 | **0** | Clean |
  | 184 | End-to-End Error | 100 | 100 | **0** | Clean |
  | 9 | Power-On Hours | 43 | 43 | **25 005** | 2.85 years spinning; normalised 43 |
  | 193 | Load/Unload Cycle Count | 41 | 41 | **599 407** | ⚠ **99.9% of rated life — see §10.8** |
  | 188 | Command Timeout | 100 | 100 | **4** | ⚠ see below |
  | 199 | UDMA CRC Error Count | 100 | 100 | **10** | ⚠ see below |

  **The media is sound** — the five attributes that actually predict platter death are all zero, so
  the 22.5 s `ReadLatencyMax` is *not* a failing surface. But two counters are non-zero and both are
  new information:
  - **199 UDMA CRC Error Count = 10** — ten corrupted transfers on the SATA link. This is a *cable,
    connector or controller* fault, never the platters. On a laptop it points at the drive's SATA
    connector or the board-side connection. It is also **permanent and cumulative**, so 10 could be
    old; what matters is whether it climbs. Re-run `-DiagnosticsOnly` after a week — a rising count
    means reseat the drive.
  - **188 Command Timeout = 4** — four commands the drive failed to answer in time. This is the
    single most direct corroboration of the multi-second stalls in §10.1: a timeout *is* a stall.
  - **187 is unreadable, not alarming.** Its raw field decodes to ~2×10¹⁴ because HGST packs vendor
    data into the upper raw bytes. Section 6.2 detects this (top two of the six raw bytes set) and
    labels the attribute `vendor-packed` rather than issuing a false warning. Use **CrystalDiskInfo**
    if you want a vendor-aware reading of it.
- ~~Battery health unmeasured~~ — **done, see §10.5.** Battery is at 77.1% and is ruled out.
- **`powercfg /hibernate on` did not take effect.** Section 6.7 run on 2026-08-05 reports
  `Hibernate — NOT available: Hibernation has not been enabled`, with Fast Startup and Hybrid
  Sleep both unavailable *because* hibernation is, and no `hiberfil.sys` on C:. Re-run
  `powercfg /hibernate /type reduced` from an **elevated** prompt and re-check with
  `-DiagnosticsOnly`. Note this means C: is **not** currently carrying a ~3 GB hiberfil — so
  the space accounting in §10.4 stands, and the §5 trade-off is not yet realised either way.
- **The SD card reader is gone from the system entirely.** `Get-PhysicalDisk` on 2026-08-05 returns
  a single row — `DeviceId 0, HGST HTS541010A9E680, OK, Healthy`. `\Device\Harddisk1\DR1`, the
  source of all 21 "bad block" errors in §2, no longer enumerates. That closes §10's disk-error
  thread: the failing device has removed itself.
- **Housekeeping:** a stray `C:\Windows\System32\battery-report.html` exists from running
  `powercfg /batteryreport` in an elevated System32 prompt (`powercfg` writes to the *current*
  directory). Harmless, ~200 KB, delete at will. The script avoids this by always passing
  `/output` with an explicit path — see `-DiagnosticsOutDir` in §9.2.
- The `Diagnostics-Performance` event log and `Get-MpComputerStatus` were not re-run; neither is
  likely to change the diagnosis.

---

### 10.8 Second elevated run — the drive is worn out *(2026-08-05, `-Diagnostics -SkipLargeFileScan`)*

This was the first run where **section 6 produced complete data**: the SMART *threshold* table
(`MSStorageDriver_FailurePredictThresholds`) requires Administrator, so until this run the `Thr`
column was empty and no threshold-based verdict was possible. With it populated, three findings
emerged that the panel had previously been blind to — and the panel has been extended to catch each
one automatically from now on.

#### The headline: 99.9% of rated head-park life

| ID | Attribute | Raw | Rating | Reading |
|---|---|---|---|---|
| 193 | Load/Unload Cycle Count | **599,407** | ~600,000 | **99.9% of rated mechanical life** |
| 4 | Start/Stop Count | 5,829 | ~50,000 | 11.7% — fine |
| 12 | Power Cycle Count | 5,786 | ~50,000 | 11.6% — fine |

Over 25,005 power-on hours that is **~24 head parks per hour — one every 2.5 minutes**, the
signature of aggressive APM idle parking. Two consequences:

- **It is a failure mode, not a slowness symptom.** Cycle counters count *normal motion*, not
  errors, so they never trip the drive's `PredictFailure` bit. The drive will report perfect health
  right up to the point the actuator stops parking reliably. **Sound media + exhausted actuator is
  precisely the profile that dies without warning.**
- **It also explains the latency maxima.** Every park/unpark stalls I/O for seconds while the heads
  reload. The 22.5 s `ReadLatencyMax` in §10.1 has a mechanical cause, not just a queueing one.

The panel previously graded this line `[    ]` — no verdict at all. It now carries `WearLimit`
metadata per attribute, expresses the raw as a percentage of the rating, and grades ≥90% as `[BAD ]`:

```
[BAD ]  193  Load/Unload Cycle Count   41  41   0  599407  (99.9% of ~600000 rated)
```

#### 8,319 physical shock events (attribute 191)

G-Sense Error Rate counts shocks the drive itself detected — the laptop being moved, bumped or
vibrated **while the platters are spinning**. Each one can force an *emergency* head unload, which
is both a multi-second stall and additional wear on the already-exhausted actuator. Until the disk
is replaced: keep the machine flat and don't move it while it is working. An SSD removes this
failure mode entirely.

#### The drive has overheated in the past (attribute 190)

```
[WARN]  190  Airflow Temperature       65  40  45  35 C
        PAST THRESHOLD BREACH (recovered -- current values are fine):
          - 190 (Airflow Temperature): worst-ever 40 vs threshold 45
```

Current value 65 is comfortably above the threshold of 45, so nothing is wrong *now*. But `Wst 40`
means the normalised value once fell **below** the drive's own limit and then recovered. A recovered
excursion leaves **no error count behind** — this is the only trace it ever happened, and the panel
was previously blind to it because it only tested the current value.

This matters beyond the disk: it is **independent physical evidence of overheating** in a machine
with 30 instant, unlogged power losses (§10.6), zero WHEA errors and a healthy battery. Two separate
subsystems now point at cooling. The fan clean and repaste in §7.4 moves up the list accordingly.

#### Attribute 192 — a false alarm, correctly suppressed

`Emergency Unload Count = 20,316,470` against a ~20,000 rating. That is not 100,000% wear; it is
HGST packing vendor data into a field this decoder cannot interpret. The existing "vendor-packed"
test misses it because the *upper* raw bytes are zero, so a second guard was added: a cycle count
more than 10× its rating is not a plain count. It renders with no verdict rather than a fabricated
end-of-life alarm:

```
[    ]  192  Emergency Unload Count    99  99   0  20316470  (implausible vs ~20000 rating -- not a plain count)
```

#### 6.1 and 6.2 disagreed by 62×, and the panel presented both as fact

Section 6.1's driver counter reported `LoadUnloadCycleCount = 9,583`; SMART attribute 193 says
**599,407**. `Get-StorageReliabilityCounter` is a driver-level summary covering what that driver has
observed; SMART reads the drive's own lifetime log. **SMART is authoritative.** The panel now
cross-checks the two and prints a note whenever they differ by more than 2×, so the smaller number
is never taken at face value.

#### Filesystem: worse than the first run

| Metric | First run | This run |
|---|---|---|
| C: fragments per file | 1.02 | **1.03** — still a non-issue |
| C: free-space fragments | 31,457 | **46,302** |
| C: largest contiguous run | — | **2.55 GB** |
| C: MFT usage | — | **100%** |
| E: MFT usage | — | **100%** |

Free space is now shattered into nearly 50% more pieces than three weeks ago, with the largest
single contiguous run at 2.55 GB. The staged ~20 GB Windows feature upgrade (§4) still has nowhere
contiguous to land. **MFT at 100% on both volumes** means the master file table has outgrown its
reserved zone, so all further metadata growth fragments — a second, independent reason the upgrade
should land on the SSD instead.

#### Still not applied

`Hibernate — NOT available` **even in this elevated session**, so `powercfg /hibernate on` has still
not been re-run (§10.7 flagged this; it remains open). Fast Startup and Hybrid Sleep are unavailable
as a consequence. The panel's advisory is correct and still applies.

#### What changed in the script as a result

| Capability added to §6.2 | Catches |
|---|---|
| `WearLimit` per cycle-counter attribute + `% of rated` rendering | Attr 193 at 99.9% — previously ungraded |
| `$wearBogus` guard (raw > 10× rating) | Attr 192's vendor-packed count — prevents a false alarm |
| `$everBreached` (`Wst <= Thr` while `Cur` is healthy) | Attr 190's past over-temperature — previously invisible |
| SHOCK EVENTS narrative (attr 191 > 1,000) | 8,319 shocks and their I/O-stall consequence |
| SMART-vs-driver LoadUnload reconciliation | The 62× discrepancy between 6.1 and 6.2 |
| Split media/wear verdict | Stops wear from masking "the platters are clean, a clone will work" |
| Low-free-space warning at the top of every run | E: at 8.9%, previously printed silently |

---

## 11. Recommended order of operations

> **Reordered 2026-08-05 after §10.8.** The drive is at 99.9% of its rated mechanical life. The
> backup is no longer just prudent and the SSD is no longer just a speed upgrade — both are now
> time-sensitive. Steps 1 and 7 are the ones with a clock on them.

1. **Back up** D: and anything on C: you care about, to an external drive. Do this before anything
   else — and now do it *this week*, not eventually. The media is clean today (§10.8), which is what
   makes a full backup and a clone still possible; a worn actuator does not give notice.
2. **Stop using the SD card slot.** Immediate relief from the freezes. Note the errors are not
   historical — the most recent one is timestamped **2026-08-05 15:43**, and the device has since
   dropped off the bus entirely. It failed *today*.
3. ~~**Reclaim the 15.1 GB search index** (§3.1).~~ ✅ **Done 2026-08-05** — C: went 16.4% → **23.6%**
   free. Nothing further to do here; the script now reports the index as absent.
4. ~~Run `pc-cleanup.ps1 -Apply` for the routine passes.~~ ✅ Done — these free ~0 KB now, because
   previous runs already took everything. `C:\$Windows.~BT` stays: Disk Cleanup declined to remove
   it (§4.1), which is the correct outcome while the upgrade is staged.
5. **Free up E:** — it is at **8.9%** free, below the ~15% where NTFS allocation quality degrades
   (§2.5). Nothing this script deletes lives there; this means moving your own files to D:, which has
   190 GB free. The script now flags this explicitly at the top of every run.
6. **Reboot.**
7. Order a **1 TB 2.5" SATA SSD** + USB-SATA adapter — **do this now, not after the other steps**
   (§10.8: the drive is at 99.9% of rated head-park life). *(Optionally 2 × 8 GB DDR3L-1600 at the
   same time.)* Until it arrives, **keep the laptop flat and don't move it while it is working** —
   attribute 191 has already logged 8,319 shock events, each one an emergency head unload.
8. Clone HDD → SSD (**keep MBR**), swap the drive, keep the HDD as backup. **While the drive is
   out, reseat the SATA connector** — SMART attribute 199 shows 10 UDMA CRC errors (§10.7), which
   are link-level faults, and a marginal connector would corrupt the SSD's transfers too.
9. **While the bottom panel is off: clean the fan/heatsink and repaste the CPU** (§7.4). Same panel
   as the drive and RAM, so it is free effort — and it is the leading fix for the 35 unexpected
   shutdowns in §10.6. This is now backed by **two independent lines of evidence**: the shutdown
   profile (instant deaths, healthy battery, zero WHEA) and SMART attribute 190's **past
   over-temperature breach** (§10.8). Measure temps with HWiNFO64 before and after.
10. Let the staged Windows feature upgrade install onto the SSD.
11. Restore Fast Startup: `powercfg /hibernate on` then `powercfg /hibernate /type reduced` —
    **from an elevated prompt**, and verify with `-DiagnosticsOnly` (§10.7: it silently did not
    take last time).
12. Optionally re-enable `WSearch` — but only *after* the SSD swap, so the full re-crawl runs on
    flash instead of a 5400 RPM platter.
13. Decide the long-term OS question (§8) at your leisure.

**Steps 3 and 4 are complete.** Everything the software side can give you has now been taken — C: is
at 23.6% free and there is no meaningful reclaim left on it. What remains open and free is step 5
(E: at 8.9%) and step 6 (reboot). **Step 7–8 is the one that actually fixes the machine**, and steps
9 and 11 ride along with it at no extra effort.

**What changed with the second elevated run (§10.8):** step 1 and step 7 now have a deadline
attached. Everything else on this list is optimisation; those two are insurance on a drive that has
spent 99.9% of its rated mechanical life. If you do nothing else this week, do the backup.
