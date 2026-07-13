# How to Shrink D: and Extend C: on a Windows GPT Disk

## Overview

Current layout:

``` text
[EFI (100 MB)] [MSR (16 MB)] [C:] [Recovery (774 MB)] [D:]
```

The Recovery partition sits between C: and D:, preventing Windows Disk
Management from extending C:.

## Do not delete these partitions

-   EFI System Partition (100 MB): required for booting.
-   Recovery Partition (774 MB): contains Windows Recovery Environment.

Delete them only during a full clean Windows installation.

## Why shrinking D: wasn't enough

Windows can only extend C: into unallocated space immediately to its
right.

Shrinking D: normally creates:

``` text
[C:] [Recovery] [D:] [Unallocated]
```

The Recovery partition blocks the extension.

## Why MiniTool couldn't resize D:

MiniTool showed both C: and D: as BitLocker volumes with 100% used.

Control Panel showed "BitLocker waiting for activation", but:

``` cmd
manage-bde -status
```

reported:

-   Conversion Status: Used Space Only Encrypted
-   Percentage Encrypted: 100%
-   Protection Status: Protection Off
-   Key Protectors: None Found

The drives were still encrypted, preventing resizing.

## Verify status

``` cmd
manage-bde -status
```

Check: - Conversion Status - Percentage Encrypted - Protection Status -
Lock Status

## Fully decrypt

``` cmd
manage-bde -off C:
manage-bde -off D:
```

Monitor:

``` cmd
manage-bde -status
```

Wait until:

``` text
Conversion Status: Fully Decrypted
Percentage Encrypted: 0.0%
```

## Pause decryption

``` cmd
manage-bde -pause C:
manage-bde -pause D:
```

Resume:

``` cmd
manage-bde -resume C:
manage-bde -resume D:
```

## Resize partitions

After decryption:

1.  Reboot.
2.  Open MiniTool Partition Wizard.
3.  Shrink D: from the left (Move/Resize).
4.  Move the Recovery partition to the right.
5.  Extend C:.
6.  Apply changes.

## Re-enable BitLocker

After confirming everything works:

-   Enable BitLocker on C:
-   Enable BitLocker on D:
-   Save recovery keys.

## Commands

Check status:

``` cmd
manage-bde -status
```

Decrypt:

``` cmd
manage-bde -off C:
manage-bde -off D:
```

Pause:

``` cmd
manage-bde -pause C:
manage-bde -pause D:
```

Resume:

``` cmd
manage-bde -resume C:
manage-bde -resume D:
```

## Safety

-   Back up important files.
-   Keep the PC plugged in.
-   Do not interrupt partition operations.
-   Do not delete the EFI or Recovery partitions unless you understand
    the consequences.
