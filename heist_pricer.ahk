script  = %a_scriptdir%\heist_ocr.py
command := "python3 "
JEE_RunGetStdOut(vTarget, vSize:="")
{
    DetectHiddenWindows, On
    vComSpec := A_ComSpec ? A_ComSpec : ComSpec
    Run, % vComSpec,, Hide, vPID
    WinWait, % "ahk_pid " vPID
    DllCall("kernel32\AttachConsole", "UInt",vPID)
    oShell := ComObjCreate("WScript.Shell")
    oExec := oShell.Exec(vTarget)
    vStdOut := ""
    if !(vSize = "")
        VarSetCapacity(vStdOut, vSize)
    while !oExec.StdOut.AtEndOfStream
        vStdOut := oExec.StdOut.ReadAll()
    DllCall("kernel32\FreeConsole")
    Process, Close, % vPID
    return vStdOut
}
Alt & F3::
F3::
{
    result := JEE_RunGetStdOut(command . script)
    MsgBox % result
}