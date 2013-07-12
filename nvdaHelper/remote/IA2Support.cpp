/*
This file is a part of the NVDA project.
URL: http://www.nvda-project.org/
Copyright 2006-2010 NVDA contributers.
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2.0, as published by
    the Free Software Foundation.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
This license can be found at:
http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
*/

#include <cstdio>
#include <cwchar>
#define WIN32_LEAN_AND_MEAN 
#include <windows.h>
#include <objbase.h>
#include <ia2.h>
#include "nvdaControllerInternal.h"
#include <common/log.h>
#include "nvdaHelperRemote.h"
#include "dllmain.h"
#include "IA2Support.h"

typedef ULONG(*LPFNDLLCANUNLOADNOW)();

#pragma data_seg(".ia2SupportShared")
wchar_t IA2DllPath[MAX_PATH]={0};
IID ia2Iids[]={
	IID_IAccessible2,
	IID_IAccessibleAction,
	IID_IAccessibleApplication,
	IID_IAccessibleComponent,
	IID_IAccessibleEditableText,
	IID_IAccessibleHyperlink,
	IID_IAccessibleHypertext,
	IID_IAccessibleImage,
	IID_IAccessibleRelation,
	IID_IAccessibleTable,
	IID_IAccessibleTable2,
	IID_IAccessibleTableCell,
	IID_IAccessibleText,
	IID_IAccessibleValue,
};
#pragma data_seg()
#pragma comment(linker, "/section:.ia2SupportShared,rws")

#define IAccessible2ProxyIID IID_IAccessible2

IID _ia2PSClsidBackups[ARRAYSIZE(ia2Iids)]={0};
bool isIA2Installed=FALSE;
HINSTANCE IA2DllHandle=0;
DWORD IA2RegCooky=0;
HANDLE IA2UIThreadHandle=NULL;
DWORD IA2UIThreadID=0;
HANDLE IA2UIThreadUninstalledEvent=NULL;
UINT wm_uninstallIA2Support=0;
bool isIA2Initialized=FALSE;

bool installIA2Support() {
	LPFNGETCLASSOBJECT IA2Dll_DllGetClassObject;
	int i;
	int res;
	if(isIA2Installed) return FALSE;
	if((IA2DllHandle=CoLoadLibrary(IA2DllPath,FALSE))==NULL) {
		LOG_ERROR(L"CoLoadLibrary failed");
		return FALSE;
	}
	IA2Dll_DllGetClassObject=(LPFNGETCLASSOBJECT)GetProcAddress(static_cast<HMODULE>(IA2DllHandle),"DllGetClassObject");
	nhAssert(IA2Dll_DllGetClassObject); //IAccessible2 proxy dll must have this function
	IUnknown* ia2ClassObjPunk=NULL;
	if((res=IA2Dll_DllGetClassObject(IAccessible2ProxyIID,IID_IUnknown,(LPVOID*)&ia2ClassObjPunk))!=S_OK) {
		LOG_ERROR(L"Error calling DllGetClassObject, code "<<res);
		CoFreeLibrary(IA2DllHandle);
		IA2DllHandle=0;
		return FALSE;
	}
	if((res=CoRegisterClassObject(IAccessible2ProxyIID,ia2ClassObjPunk,CLSCTX_INPROC_SERVER,REGCLS_MULTIPLEUSE,(LPDWORD)&IA2RegCooky))!=S_OK) {
		LOG_DEBUGWARNING(L"Error registering class object, code "<<res);
		ia2ClassObjPunk->Release();
		CoFreeLibrary(IA2DllHandle);
		IA2DllHandle=0;
		return FALSE;
	}
	ia2ClassObjPunk->Release();
	for(i=0;i<ARRAYSIZE(ia2Iids);++i) {
		CoGetPSClsid(ia2Iids[i],&(_ia2PSClsidBackups[i]));
		CoRegisterPSClsid(ia2Iids[i],IAccessible2ProxyIID);
	}
	isIA2Installed=TRUE;
	return TRUE;
}

bool uninstallIA2Support() {
	int i;
	LPFNDLLCANUNLOADNOW IA2Dll_DllCanUnloadNow;
	if(!isIA2Installed)
		return FALSE;
	for(i=0;i<ARRAYSIZE(ia2Iids);++i) {
		CoRegisterPSClsid(ia2Iids[i],_ia2PSClsidBackups[i]);
	}
	CoRevokeClassObject(IA2RegCooky);
	IA2Dll_DllCanUnloadNow=(LPFNDLLCANUNLOADNOW)GetProcAddress(static_cast<HMODULE>(IA2DllHandle),"DllCanUnloadNow");
	nhAssert(IA2Dll_DllCanUnloadNow); //IAccessible2 proxy dll must have this function
	if(IA2Dll_DllCanUnloadNow()==S_OK) {
		CoFreeLibrary(IA2DllHandle);
	}
	IA2DllHandle=0;
	isIA2Installed=FALSE;
	return TRUE;
}

bool IA2Support_initialize() {
	nhAssert(!isIA2Initialized);
	wsprintf(IA2DllPath,L"%s\\IAccessible2Proxy.dll",dllDirectory);
	isIA2Initialized=TRUE;
	return TRUE;
}

void CALLBACK IA2Support_winEventProcHook(HWINEVENTHOOK hookID, DWORD eventID, HWND hwnd, long objectID, long childID, DWORD threadID, DWORD time) { 
	if (eventID != EVENT_SYSTEM_FOREGROUND && eventID != EVENT_OBJECT_FOCUS)
		return;
	if (installIA2Support()) {
		IA2UIThreadHandle=OpenThread(SYNCHRONIZE,false,threadID);
		IA2UIThreadID=threadID;
		// IA2 support successfully installed, so this hook isn't needed anymore.
		unregisterWinEventHook(IA2Support_winEventProcHook);
	}
}

LRESULT CALLBACK IA2Support_uninstallerHook(int code, WPARAM wParam, LPARAM lParam) {
	MSG* pmsg=(MSG*)lParam;
	if(pmsg->message==wm_uninstallIA2Support) {
		uninstallIA2Support();
		SetEvent(IA2UIThreadUninstalledEvent);
	}
	return 0;
}

void IA2Support_inProcess_initialize() {
	if (isIA2Installed)
		return;
	// Try to install IA2 support on focus/foreground changes.
	// This hook will be unregistered by the callback once IA2 support is successfully installed.
	registerWinEventHook(IA2Support_winEventProcHook);
}

void IA2Support_inProcess_terminate() {
	// This will do nothing if the hook isn't registered.
	unregisterWinEventHook(IA2Support_winEventProcHook);
	if(!isIA2Installed||!IA2UIThreadHandle) {
		return;
	}
	//Check if the UI thread is still alive, if not there's nothing for us to do
	if(WaitForSingleObject(IA2UIThreadHandle,0)==0) {
		return;
	}
	//Instruct the UI thread to uninstall IA2
	IA2UIThreadUninstalledEvent=CreateEvent(NULL,true,false,NULL);
	registerWindowsHook(WH_GETMESSAGE,IA2Support_uninstallerHook);
	wm_uninstallIA2Support=RegisterWindowMessage(L"wm_uninstallIA2Support");
	PostThreadMessage(IA2UIThreadID,wm_uninstallIA2Support,0,0);
	HANDLE waitHandles[2]={IA2UIThreadUninstalledEvent,IA2UIThreadHandle};
	int res=WaitForMultipleObjects(2,waitHandles,false,10000);
	if(res!=WAIT_OBJECT_0&&res!=WAIT_OBJECT_0+1) {
		LOG_DEBUGWARNING(L"WaitForMultipleObjects returned "<<res);
	}
	unregisterWindowsHook(WH_GETMESSAGE,IA2Support_uninstallerHook);
	CloseHandle(IA2UIThreadUninstalledEvent);
	CloseHandle(IA2UIThreadHandle);
}
