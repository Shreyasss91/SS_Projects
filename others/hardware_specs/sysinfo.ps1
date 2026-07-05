# ============================================================================
# Hardware Inventory Report
# ============================================================================
$outputFile = "$PSScriptRoot\Hardware_Report.txt"

Start-Transcript -Path $outputFile -Force

try {

Write-Host "============================================================================="
Write-Host "                    HARDWARE INVENTORY REPORT"
Write-Host "============================================================================="

#------------------------------------------------------------------------------
# Computer System
#------------------------------------------------------------------------------
$cs = Get-CimInstance Win32_ComputerSystem

Write-Host "`n================ COMPUTER SYSTEM ================"
$cs | Select-Object `
    Name,
    Manufacturer,
    Model,
    SystemFamily,
    SystemType,
    Domain,
    TotalPhysicalMemory,
    NumberOfProcessors,
    NumberOfLogicalProcessors |
Format-List

#------------------------------------------------------------------------------
# Computer System Product
#------------------------------------------------------------------------------
Write-Host "`n================ COMPUTER SYSTEM PRODUCT ================"

Get-CimInstance Win32_ComputerSystemProduct |
Select-Object `
    Vendor,
    Name,
    Version,
    IdentifyingNumber,
    UUID |
Format-List

#------------------------------------------------------------------------------
# BIOS
#------------------------------------------------------------------------------
Write-Host "`n================ BIOS ================"

Get-CimInstance Win32_BIOS |
Select-Object `
    Manufacturer,
    SMBIOSBIOSVersion,
    Version,
    ReleaseDate,
    SerialNumber |
Format-List

#------------------------------------------------------------------------------
# Motherboard
#------------------------------------------------------------------------------
Write-Host "`n================ MOTHERBOARD ================"

Get-CimInstance Win32_BaseBoard |
Select-Object `
    Manufacturer,
    Product,
    Version,
    SerialNumber |
Format-List

#------------------------------------------------------------------------------
# Processor
#------------------------------------------------------------------------------
Write-Host "`n================ PROCESSOR ================"

Get-CimInstance Win32_Processor |
Select-Object `
    DeviceID,
    Name,
    Manufacturer,
    Description,
    SocketDesignation,
    ProcessorId,
    Architecture,
    Family,
    NumberOfCores,
    NumberOfLogicalProcessors,
    MaxClockSpeed,
    CurrentClockSpeed,
    L2CacheSize,
    L3CacheSize,
    AddressWidth,
    DataWidth,
    ExtClock,
    VirtualizationFirmwareEnabled,
    VMMonitorModeExtensions,
    SecondLevelAddressTranslationExtensions,
    DataExecutionPreventionAvailable |
Format-List

#------------------------------------------------------------------------------
# Operating System Memory
#------------------------------------------------------------------------------
Write-Host "`n================ MEMORY STATUS ================"

$os = Get-CimInstance Win32_OperatingSystem

$totalRAM = [math]::Round($cs.TotalPhysicalMemory/1GB,2)

$totalPhysicalMB = [math]::Round($os.TotalVisibleMemorySize/1024,0)
$freePhysicalMB = [math]::Round($os.FreePhysicalMemory/1024,0)

$totalVirtualMB = [math]::Round($os.TotalVirtualMemorySize/1024,0)
$freeVirtualMB = [math]::Round($os.FreeVirtualMemory/1024,0)

$pageMB = [math]::Round($os.SizeStoredInPagingFiles/1024,0)

Write-Host "Installed RAM            : $totalRAM GB"
Write-Host "Visible Physical Memory  : $totalPhysicalMB MB"
Write-Host "Free Physical Memory     : $freePhysicalMB MB"
Write-Host "Used Physical Memory     : $($totalPhysicalMB-$freePhysicalMB) MB"
Write-Host "Total Virtual Memory     : $totalVirtualMB MB"
Write-Host "Free Virtual Memory      : $freeVirtualMB MB"
Write-Host "Used Virtual Memory      : $($totalVirtualMB-$freeVirtualMB) MB"
Write-Host "Paging File Size         : $pageMB MB"

#------------------------------------------------------------------------------
# Physical Memory Modules
#------------------------------------------------------------------------------
Write-Host "`n================ MEMORY MODULES ================"

Get-CimInstance Win32_PhysicalMemory |
Select-Object `
    BankLabel,
    DeviceLocator,
    Manufacturer,
    PartNumber,
    SerialNumber,
    FormFactor,
    MemoryType,
    SMBIOSMemoryType,
    Capacity,
    Speed,
    ConfiguredClockSpeed,
    ConfiguredVoltage,
    DataWidth,
    TotalWidth |
Format-Table -AutoSize

#------------------------------------------------------------------------------
# Memory Array
#------------------------------------------------------------------------------
Write-Host "`n================ MEMORY ARRAY ================"

Get-CimInstance Win32_PhysicalMemoryArray |
Select-Object `
    MaxCapacity,
    MaxCapacityEx,
    MemoryDevices,
    Use,
    Location |
Format-List

#------------------------------------------------------------------------------
# Page File
#------------------------------------------------------------------------------
Write-Host "`n================ PAGE FILE ================"

Get-CimInstance Win32_PageFileUsage |
Select-Object `
    Name,
    AllocatedBaseSize,
    CurrentUsage,
    PeakUsage,
    TempPageFile |
Format-Table -AutoSize

#------------------------------------------------------------------------------
# Physical Disks
#------------------------------------------------------------------------------
Write-Host "`n================ PHYSICAL DISKS ================"

Get-CimInstance Win32_DiskDrive |
Select-Object `
    Index,
    Model,
    Manufacturer,
    InterfaceType,
    MediaType,
    SerialNumber,
    FirmwareRevision,
    Partitions,
    Size,
    BytesPerSector,
    SectorsPerTrack,
    TracksPerCylinder,
    TotalCylinders,
    Status |
Format-List

#------------------------------------------------------------------------------
# Disk Partitions
#------------------------------------------------------------------------------
Write-Host "`n================ PARTITIONS ================"

Get-CimInstance Win32_DiskPartition |
Select-Object `
    DiskIndex,
    Index,
    Type,
    BootPartition,
    Bootable,
    PrimaryPartition,
    Size |
Format-Table -AutoSize

#------------------------------------------------------------------------------
# Logical Disks
#------------------------------------------------------------------------------
Write-Host "`n================ LOGICAL DISKS ================"

Get-CimInstance Win32_LogicalDisk |
Where-Object DriveType -eq 3 |
Select-Object `
    DeviceID,
    VolumeName,
    FileSystem,
    VolumeSerialNumber,
    @{
        Name="Size(GB)"
        Expression={[math]::Round($_.Size/1GB,2)}
    },
    @{
        Name="Free(GB)"
        Expression={[math]::Round($_.FreeSpace/1GB,2)}
    },
    @{
        Name="Used(GB)"
        Expression={[math]::Round(($_.Size-$_.FreeSpace)/1GB,2)}
    } |
Format-Table -AutoSize

#------------------------------------------------------------------------------
# Disk Volumes
#------------------------------------------------------------------------------
Write-Host "`n================ VOLUMES ================"

Get-CimInstance Win32_Volume |
Where-Object DriveType -eq 3 |
Select-Object `
    DriveLetter,
    Label,
    FileSystem,
    Capacity,
    FreeSpace,
    BootVolume,
    SystemVolume |
Format-Table -AutoSize

#------------------------------------------------------------------------------
# Graphics / GPU
#------------------------------------------------------------------------------
Write-Host "`n================ GRAPHICS ADAPTERS ================"

Get-CimInstance Win32_VideoController |
Select-Object `
    Name,
    VideoProcessor,
    AdapterCompatibility,
    DriverVersion,
    DriverDate,
    VideoModeDescription,
    CurrentHorizontalResolution,
    CurrentVerticalResolution,
    CurrentRefreshRate,
    CurrentBitsPerPixel,
    @{
        Name="AdapterRAM(GB)"
        Expression={
            if ($_.AdapterRAM) {
                [math]::Round($_.AdapterRAM / 1GB,2)
            }
        }
    },
    PNPDeviceID,
    Status |
Format-List
#------------------------------------------------------------------------------
# Display Drivers
#------------------------------------------------------------------------------
Write-Host "`n================ DISPLAY DRIVERS ================"

Get-CimInstance Win32_PnPSignedDriver |
Where-Object {
    $_.DeviceClass -eq "DISPLAY"
} |
Select-Object `
    DeviceName,
    Manufacturer,
    DriverVersion,
    DriverDate,
    DriverProviderName,
    InfName,
    IsSigned |
Format-Table -AutoSize
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
}
finally {

Stop-Transcript

Write-Host ""
Write-Host "Report saved to:"
Write-Host $outputFile

}