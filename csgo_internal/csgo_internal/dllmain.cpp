#include <Windows.h>
#include <string>
#include <iostream>
#include <thread>
#include <tlhelp32.h>
#include <gdiplus.h>
#include <time.h>
#include <chrono>
#include <fstream>
#include <sstream>
#include <iomanip>


const LPCWSTR GameTitle = L"Counter-Strike: Global Offensive";

const DWORD dwViewMatrix = 81473700;
const DWORD dwEntityList = 81532812;
const DWORD m_bDormant = 237;
const DWORD m_iTeamNum = 244;
const DWORD m_vecOrigin = 312;
const DWORD m_dwBoneMatrix = 9896;
const DWORD m_bSpotted = 2365;

int GetEncoderClsid(const WCHAR* format, CLSID* pClsid) {
	using namespace Gdiplus;
	UINT  num = 0;
	UINT  size = 0;

	ImageCodecInfo* pImageCodecInfo = NULL;

	GetImageEncodersSize(&num, &size);
	if (size == 0)
		return -1;

	pImageCodecInfo = (ImageCodecInfo*)(malloc(size));
	if (pImageCodecInfo == NULL)
		return -1;

	GetImageEncoders(num, size, pImageCodecInfo);
	for (UINT j = 0; j < num; ++j)
	{
		if (wcscmp(pImageCodecInfo[j].MimeType, format) == 0)
		{
			*pClsid = pImageCodecInfo[j].Clsid;
			free(pImageCodecInfo);
			return j;
		}
	}
	free(pImageCodecInfo);
	return 0;
}

void gdiscreen(int x, int y, int w, int h, const WCHAR* name) {
	using namespace Gdiplus;
	IStream* istream;
	HRESULT res = CreateStreamOnHGlobal(NULL, true, &istream);
	GdiplusStartupInput gdiplusStartupInput;
	ULONG_PTR gdiplusToken;
	GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
	{
		HDC scrdc, memdc;
		HBITMAP membit;
		scrdc = ::GetDC(0);
		int Height = GetSystemMetrics(SM_CYSCREEN);
		int Width = GetSystemMetrics(SM_CXSCREEN);
		memdc = CreateCompatibleDC(scrdc);
		membit = CreateCompatibleBitmap(scrdc, w, h);
		HBITMAP hOldBitmap = (HBITMAP)SelectObject(memdc, membit);
		//BitBlt(memdc, 0, 0, 600, 600, scrdc, Width / 2 - 300, Height / 2 - 300, SRCCOPY);
		BitBlt(memdc, 0, 0, w, h, scrdc, x, y, SRCCOPY);

		Gdiplus::Bitmap bitmap(membit, NULL);
		CLSID clsid;
		GetEncoderClsid(L"image/jpeg", &clsid);
		bitmap.Save(name, &clsid, NULL); // To save the jpeg to a file
		//bitmap.Save(istream, &clsid, NULL);

		// Create a bitmap from the stream and save it to make sure the stream has the image
//		Gdiplus::Bitmap bmp(istream, NULL);
//		bmp.Save(L"t1est.jpeg", &clsid, NULL);             
		// END
		DeleteObject(memdc);
		DeleteObject(membit);
		::ReleaseDC(0, scrdc);
	}
	GdiplusShutdown(gdiplusToken);

	istream->Release();
}
struct ViewMatrix
{
	float viewMatrix[16];
};
struct vec3
{
	float x;
	float y;
	float z;
};
struct vec2
{
	float x;
	float y;
};
struct head_bone
{
	float x() { return *(float*)(this + (8 * 0x30) + 0x0C); }
	float y() { return *(float*)(this + (8 * 0x30) + 0x1C); }
	float z() { return *(float*)(this + (8 * 0x30) + 0x2C); }
};
struct Entity
{
	int dormant() { return *(int*)(this + m_bDormant); }
	int team() { return *(int*)(this + m_iTeamNum); }
	vec3* position() { return (vec3*)(this + m_vecOrigin); }
	bool spotted() { return *(bool*)(this + m_bSpotted); }
	head_bone* headpos() { return *(head_bone**)(this + m_dwBoneMatrix); }
};


void WorldToScreen(vec3* pos, ViewMatrix* vm, vec3* pos2d)
{
	float clip_x = pos->x * vm->viewMatrix[0] + pos->y * vm->viewMatrix[1] + pos->z * vm->viewMatrix[2] + 1 * vm->viewMatrix[3];
	float clip_y = pos->x * vm->viewMatrix[4] + pos->y * vm->viewMatrix[5] + pos->z * vm->viewMatrix[6] + 1 * vm->viewMatrix[7];
	float clip_z = pos->x * vm->viewMatrix[12] + pos->y * vm->viewMatrix[13] + pos->z * vm->viewMatrix[14] + 1 * vm->viewMatrix[15];
	float Height = GetSystemMetrics(SM_CYSCREEN);
	float Width = GetSystemMetrics(SM_CXSCREEN);
	//std::cout << Height / 2 << std::endl;
	//std::cout << Width / 2 << std::endl;
	float ndc_x = clip_x / clip_z;
	float ndc_y = clip_y / clip_z;
	//std::cout << ndc_x << std::endl;
	//std::cout << ndc_y << std::endl;
	pos2d->x = (Width / 2.0 * ndc_x) + (ndc_x + Width / 2.0);
	pos2d->y = (Height / 2.0 * ndc_y) + (ndc_y + Height / 2.0);
	pos2d->z = clip_z;
}


void create_xml(int width, int height, int xmin1, int ymin1, int xmax1, int ymax1, int xmin2, int ymin2, int xmax2, int ymax2, const WCHAR* folder, const WCHAR* filename, const WCHAR* path, const WCHAR* box1, const WCHAR* box2, const WCHAR* outfile_name)
{
	std::wofstream outfile(outfile_name);
	outfile << "<annotation>" << std::endl;
		outfile << "\t<folder>" << folder << "</folder>" << std::endl;
		outfile << "\t<filename>" << filename << "</filename>" << std::endl;
		outfile << "\t<path>" << path << "</path>" << std::endl;
		outfile << "\t<source>" << std::endl;
			outfile << "\t\t<database>" << "Unknown" << "</database>" << std::endl;
		outfile << "\t</source>" << std::endl;
		outfile << "\t<size>" << std::endl;
			outfile << "\t\t<width>" << width << "</width>" << std::endl;
			outfile << "\t\t<height>" << height << "</height>" << std::endl;
			outfile << "\t\t<depth>" << 3 << "</depth>" << std::endl;
		outfile << "\t</size>" << std::endl;
		outfile << "\t<segmented>" << "0" << "</segmented>" << std::endl;
		outfile << "\t<object>" << std::endl;
			outfile << "\t\t<name>" << box1 << "</name>" << std::endl;
			outfile << "\t\t<pose>" << "Unspecified" << "</pose>" << std::endl;
			outfile << "\t\t<truncated>" << "0" << "</truncated>" << std::endl;
			outfile << "\t\t<difficult>" << "0" << "</difficult>" << std::endl;
			outfile << "\t\t<bndbox>" << std::endl;
				outfile << "\t\t\t<xmin>" << xmin1 << "</xmin>" << std::endl;
				outfile << "\t\t\t<ymin>" << ymin1 << "</ymin>" << std::endl;
				outfile << "\t\t\t<xmax>" << xmax1 << "</xmax>" << std::endl;
				outfile << "\t\t\t<ymax>" << ymax1 << "</ymax>" << std::endl;
			outfile << "\t\t</bndbox>" << std::endl;
		outfile << "\t</object>" << std::endl;
		outfile << "\t<object>" << std::endl;
			outfile << "\t\t<name>" << box2 << "</name>" << std::endl;
			outfile << "\t\t<pose>" << "Unspecified" << "</pose>" << std::endl;
			outfile << "\t\t<truncated>" << "0" << "</truncated>" << std::endl;
			outfile << "\t\t<difficult>" << "0" << "</difficult>" << std::endl;
			outfile << "\t\t<bndbox>" << std::endl;
				outfile << "\t\t\t<xmin>" << xmin2 << "</xmin>" << std::endl;
				outfile << "\t\t\t<ymin>" << ymin2 << "</ymin>" << std::endl;
				outfile << "\t\t\t<xmax>" << xmax2 << "</xmax>" << std::endl;
				outfile << "\t\t\t<ymax>" << ymax2 << "</ymax>" << std::endl;
			outfile << "\t\t</bndbox>" << std::endl;
		outfile << "\t</object>" << std::endl;
	outfile << "</annotation>" << std::endl;

	outfile.close();
}


DWORD GetModuleBase(DWORD processId, const TCHAR* szModuleName)
{
	DWORD moduleBase = 0;
	HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, processId);
	if (hSnapshot != INVALID_HANDLE_VALUE) {
		MODULEENTRY32 moduleEntry;
		moduleEntry.dwSize = sizeof(MODULEENTRY32);
		if (Module32First(hSnapshot, &moduleEntry)) {
			do {
				if (wcscmp((const wchar_t*)moduleEntry.szModule, (const wchar_t*)szModuleName) == 0) {
					moduleBase = (DWORD)moduleEntry.modBaseAddr;
					break;
				}
			} while (Module32Next(hSnapshot, &moduleEntry));
		}
		CloseHandle(hSnapshot);
	}
	return moduleBase;
}


int count = 6000;

void update(DWORD dllBase)
{

	ViewMatrix* vMatrix = (ViewMatrix*)(dllBase + dwViewMatrix);

	for (int i = 0; i < 128; i+=16)
	{
		Entity* entity = *(Entity**)(dllBase + dwEntityList + i);
		if (entity != NULL) {
			if (entity->dormant() == 0) {
				/*
				std::cout << "Address: " << std::hex << dllBase + dwEntityList + i << std::endl;
				std::cout << "Position: " << std::dec << entity->position()->x << std::endl;
				*/

				//entity->position()->z -= 5;

				vec3 pos2d = { 0 };
				vec3 headpos2d = { 0 };
				vec3 headpos2d2 = { 0 };

				vec3 pos;
				pos.x = entity->position()->x; pos.y = entity->position()->y; pos.z = entity->position()->z;

				pos.z -= 5;

				WorldToScreen(&pos, vMatrix, &pos2d);

				if (entity->headpos() != NULL) {
					/*
					std::cout << "Address: " << std::hex << dllBase + dwEntityList + i << std::endl;
					std::cout << "Head Address: " << std::hex << entity->headpos() << std::endl;
					std::cout << "Head Position: " << std::dec << entity->headpos()->x() << std::endl;
					std::cout << "Head Position: " << std::dec << entity->headpos()->y() << std::endl;
					std::cout << "Head Position: " << std::dec << entity->headpos()->z() << std::endl;*/
					/*
					std::cout << "Address: " << std::hex << dllBase + dwEntityList + i << std::endl;
					std::cout << "Address: " << std::hex << entity->headpos() << std::endl;
					std::cout << "Position: " << std::dec << entity->position()->x << std::endl;
					std::cout << "Position: " << std::dec << entity->position()->y << std::endl;
					std::cout << "Position: " << std::dec << entity->position()->z << std::endl;*/
					
					vec3 headpos;
					headpos.x = entity->headpos()->x(); headpos.y = entity->headpos()->y(); headpos.z = entity->headpos()->z();
					headpos.z += 8;

					WorldToScreen(&headpos, vMatrix, &headpos2d);
					headpos.z -= 8;
					WorldToScreen(&headpos, vMatrix, &headpos2d2);
					/*
					std::cout << vMatrix->viewMatrix[0] << " " << vMatrix->viewMatrix[1] << " " << vMatrix->viewMatrix[2] << " " << vMatrix->viewMatrix[3] << " " <<
						vMatrix->viewMatrix[4] << " " << vMatrix->viewMatrix[5] << " " << vMatrix->viewMatrix[6] << " " << vMatrix->viewMatrix[7] << " " <<
						vMatrix->viewMatrix[8] << " " << vMatrix->viewMatrix[9] << " " << vMatrix->viewMatrix[10] << " " << vMatrix->viewMatrix[11] << " " <<
						vMatrix->viewMatrix[12] << " " << vMatrix->viewMatrix[13] << " " << vMatrix->viewMatrix[14] << " " << vMatrix->viewMatrix[15] << std::endl;
					*/
					bool spotted = entity->spotted();


					if (spotted == true && pos2d.z > 0.2) {
						float y_distance = headpos2d.y - pos2d.y;
						float ratio = 0.28;
						float hratio = 0.1;

						float x = pos2d.x - (ratio * y_distance);
						float y = pos2d.y;
						float x2 = pos2d.x + (ratio * y_distance);
						float y2 = headpos2d.y;
						float hx = headpos2d2.x - (hratio * y_distance);
						float hy = headpos2d2.y - (hratio * y_distance);
						float hx2 = headpos2d2.x + (hratio * y_distance);
						float hy2 = headpos2d2.y + (hratio * y_distance);

						float w_player = x2 - x;
						float h_player = y2 - y;

						

						if (x > 0 && y > 0 && w_player > 0 && h_player > 0) {

							int w = 600;
							int h = 600;



							std::wostringstream ss;
							ss << std::setw(6) << std::setfill(L'00000') << count;
							std::wstring str = ss.str();

							std::wstring path = L"";
							std::wstring curr = L"img" + str;
							std::wstring filename = curr + L".jpg";
							std::wstring folder = L"training";
							std::wstring box1 = L"ct_body";
							std::wstring box2 = L"ct_head";
							//std::wstring outfile = path + curr + L".xml";
							std::wstring outfile = L"" + curr + L".xml";
							//std::wstring outfile_ss = path + filename;
							std::wstring outfile_ss = L"" + curr + L".jpg";
							float Height = GetSystemMetrics(SM_CYSCREEN);
							float Width = GetSystemMetrics(SM_CXSCREEN);

							float cx = x - (Width / 2 - w / 2);
							float cy = h - (y - (Height / 2 - h / 2));
							float cx2 = x2 - (Width / 2 - w / 2);
							float cy2 = h - (y2 - (Height / 2 - h / 2));

							float hcx = hx - (Width / 2 - w / 2);
							float hcy = h - (hy - (Height / 2 - h / 2));
							float hcx2 = hx2 - (Width / 2 - w / 2);
							float hcy2 = h - (hy2 - (Height / 2 - h / 2));


							//if (cx2 >= w) {
							//	cx2 = w - 1;
							//}
							//if (cy2 >= h) {
							//	cy2 = h - 1;
							//}




							if (cx > 0 && cx < w && cy > 0 && cy < h) {
								std::cout << std::dec << "x: " << x << std::endl;
								std::cout << std::dec << "y: " << y << std::endl;
								std::cout << std::dec << "w: " << w << std::endl;
								std::cout << std::dec << "h: " << h << std::endl;
								gdiscreen(Width / 2 - w / 2, Height / 2 - h / 2, w, h, outfile_ss.c_str());
								
								create_xml(
									w, h,
									cx, cy, cx2, cy2,
									hcx, hcy, hcx2, hcy2,
									folder.c_str(),
									filename.c_str(),
									path.c_str(),
									box1.c_str(),
									box2.c_str(),
									outfile.c_str()
								);
								

								count++;

							}


						}


					}

				}


				/*
				std::cout << "Address: " << std::hex << &pos2d << std::endl;
				std::cout << "Position2D: " << std::dec << pos2d.x << std::endl;*/
			}
		}
		
	}

	/*
	Entity* entity = *(Entity**)(dllBase + dwEntityList);

	std::cout << std::dec << entity->position()->x << std::endl;
	*/

}

int main()
{

	AllocConsole();
	freopen_s((FILE**)stdout, "CONOUT$", "w", stdout);

	HWND hwnd = FindWindowW(NULL, GameTitle);

	DWORD pid = GetProcessId(hwnd);

	LPCWSTR clientdll = L"client.dll";

	DWORD dllBase = GetModuleBase(pid, clientdll);

	std::cout << std::hex << dllBase << std::endl;

	std::cout << std::hex << dllBase + dwEntityList << std::endl;
	
	while (true) {
		update(dllBase);
		std::this_thread::sleep_for(std::chrono::milliseconds(2000));
	}
	
	
	/*
	clock_t t1 = clock();
	int i;
	int iterations = 10;
	for (i = 0; i < iterations; i++) {
		//gdiscreen(1160, 254, 165, 331, L"test.jpg");
		float Height = GetSystemMetrics(SM_CYSCREEN);
		float Width = GetSystemMetrics(SM_CXSCREEN);
		gdiscreen(Width / 2 - 200, Height / 2 - 200, 400, 400, L"test.jpg");
	}
	clock_t t2 = clock();
	printf("%d iterations: %0.0f fps\n", iterations, iterations / ((double)(t2 - t1) / CLOCKS_PER_SEC));


	create_xml(
		600, 600,
		225, 246, 251, 296,
		227, 246, 239, 256,
		L"training",
		L"img0005.jpg",
		L"C:\\Users\\jacob\\Documents\\Projects\\CSGO_Train\\training\\img0005.jpg",
		L"ct_body",
		L"ct_head"

	);*/
	
	return 0;



}

BOOL APIENTRY DllMain(HMODULE hModule,
	DWORD  ul_reason_for_call,
	LPVOID lpReserved
)
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH: {

		CreateThread(NULL, NULL, (LPTHREAD_START_ROUTINE)main, NULL, NULL, NULL);
		break;
	}

	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;
}