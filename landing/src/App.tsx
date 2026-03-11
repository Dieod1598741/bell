import { Monitor, ShieldAlert, Zap, Bell as BellIcon, CheckCircle } from 'lucide-react'
import { useState, useEffect } from 'react'

function App() {
    const [latestVersion, setLatestVersion] = useState<string>('...')

    useEffect(() => {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 5000)

        // /api/version: Cloudflare Pages Function이 GitHub API를 서버 사이드에서 캐싱
        fetch('/api/version', { signal: controller.signal })
            .then(r => r.json())
            .then(data => setLatestVersion(data.version || '최신'))
            .catch(() => setLatestVersion('최신'))
            .finally(() => clearTimeout(timeout))
    }, [])

    const downloadLinks = {
        macos: "https://github.com/Dieod1598741/bell/releases/latest/download/Bell.dmg",
        windows: "https://github.com/Dieod1598741/bell/releases/latest/download/Bell.exe"
    }

    return (
        <div className="min-h-screen bg-white text-slate-900 flex flex-col items-center justify-center p-6 font-sans">
            <div className="max-w-xl w-full text-center space-y-8">

                {/* Header */}
                <div className="space-y-2 animate-fade-in-up delay-100">
                    <h1 className="text-4xl font-black tracking-tight text-slate-900">Bell</h1>
                    <p className="text-slate-500 font-medium">사내 메신저</p>
                </div>

                {/* Download Buttons */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in-up delay-200">
                    <a
                        href={downloadLinks.macos}
                        className="flex flex-col items-center gap-3 p-6 bg-slate-900 text-white rounded-2xl hover:bg-slate-800 transition-all active:scale-95"
                    >
                        <Monitor size={32} />
                        <div className="text-center">
                            <div className="font-bold">macOS 전용</div>
                            <div className="text-xs text-slate-400">.dmg 다운로드</div>
                        </div>
                    </a>

                    <a
                        href={downloadLinks.windows}
                        className="flex flex-col items-center gap-3 p-6 border-2 border-slate-200 rounded-2xl hover:border-slate-400 transition-all active:scale-95 text-slate-900"
                    >
                        <Monitor size={32} />
                        <div className="text-center">
                            <div className="font-bold">Windows 전용</div>
                            <div className="text-xs text-slate-500">.exe 다운로드</div>
                        </div>
                    </a>
                </div>

                {/* Version Badge */}
                <div className="animate-fade-in-up delay-250">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-full text-xs text-slate-500">
                        <span className="w-2 h-2 rounded-full bg-green-400 inline-block"></span>
                        최신 버전: <strong className="text-slate-700">{latestVersion}</strong>
                    </span>
                </div>

                {/* What's New — 버전별 업데이트 내역 */}
                <div className="p-6 bg-blue-50 rounded-2xl border border-blue-100 text-left animate-fade-in-up delay-250">
                    <div className="flex items-center gap-2 text-blue-700 font-bold mb-4">
                        <Zap size={20} />
                        <span>업데이트 내역</span>
                    </div>

                    {/* v1.1.77 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-700 text-white text-xs font-bold rounded mb-2">v1.1.77</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>Windows 토스트 알림 강화</strong> — winotify → plyer → win10toast → ctypes 4단계 폴백</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>macOS 알림 특수문자</strong> — osascript 따옴표 이스케이프 수정</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.76 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-700 text-white text-xs font-bold rounded mb-2">v1.1.76</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>뱃지 실시간 갱신</strong> — SYSTEM 이벤트 count 수신해 즉시 반영</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>중복 세션 복원 제거</strong> — watch(isLoggedIn)에서 restoreSession 호출 제거</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.75 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded mb-2">v1.1.75</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>Windows 재실행 자동 로그인 안정화</strong> — LoginView 중복 자동 로그인 제거</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.73~74 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded mb-2">v1.1.73–74</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>세션 흰 화면 방지</strong> — API 타임아웃 6초·실패 시 /login 이동</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>Windows 인앱 업데이트</strong> — NSIS 인스톨러·portable exe 자동 구분</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.72 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded mb-2">v1.1.72</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>읽음 뱃지 즉시 소거</strong> — 채팅·쪽지 열면 즉시 배지 숫자 제거</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>채팅창 진입 시 일괄 읽음 처리</strong> — 미읽은 메시지 자동 읽음 처리</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>읽음 DB 컬럼 통일</strong> — read/read_at 불일치 버그 수정</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.71 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-500 text-white text-xs font-bold rounded mb-2">v1.1.71</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>쪽지 실시간 수신</strong> — 다른 PC에서 보낸 쪽지 2초 이내 수신함 반영</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>수신자 필터링</strong> — 나에게 온 쪽지만 정확히 표시</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.70 */}
                    <div className="mb-4">
                        <span className="inline-block px-2 py-0.5 bg-blue-400 text-white text-xs font-bold rounded mb-2">v1.1.70</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>채팅 실시간 수신</strong> — 상대방 메시지 2초 이내 대화창 즉시 반영</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>SSE 전체 점검</strong> — HTTP SSE 타입 버그·재연결 로직 수정</span>
                            </li>
                        </ul>
                    </div>

                    {/* v1.1.69 */}
                    <div>
                        <span className="inline-block px-2 py-0.5 bg-slate-400 text-white text-xs font-bold rounded mb-2">v1.1.69</span>
                        <ul className="space-y-1.5 text-sm text-blue-800">
                            <li className="flex items-start gap-2">
                                <CheckCircle size={14} className="mt-0.5 shrink-0 text-blue-500" />
                                <span><strong>Windows 토스트 알림</strong> · <strong>세션 유지</strong> · <strong>인앱 자동 업데이트</strong></span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* macOS 실행 가이드 */}
                <div className="p-6 bg-amber-50 rounded-2xl border border-amber-100 text-left animate-fade-in-up delay-300">
                    <div className="flex items-center gap-2 text-amber-700 font-bold mb-3">
                        <ShieldAlert size={20} />
                        <span>macOS 실행 가이드</span>
                    </div>
                    <p className="text-sm text-amber-800 leading-relaxed">
                        처음 실행 시 "확인할 수 없는 개발자" 경고가 뜨면 <strong>[시스템 설정] &gt; [개인정보 보호 및 보안]</strong> 하단에서 <strong>[확인 없이 열기]</strong>를 눌러주세요.
                    </p>
                </div>

                {/* Windows 알림 가이드 */}
                <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 text-left animate-fade-in-up delay-350">
                    <div className="flex items-center gap-2 text-slate-700 font-bold mb-3">
                        <BellIcon size={20} />
                        <span>Windows 알림 가이드</span>
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed">
                        알림이 뜨지 않으면 <strong>[설정] &gt; [시스템] &gt; [알림]</strong>에서 Bell 앱 알림이 켜져 있는지 확인해주세요. 포커스 어시스트가 켜져 있으면 알림이 차단될 수 있습니다.
                    </p>
                </div>

                {/* Footer */}
                <footer className="pt-8 text-xs text-slate-400 border-t border-slate-100 animate-fade-in-up delay-400">
                    © 2026 Bell Project. All rights reserved.
                </footer>

            </div>
        </div>
    )
}

export default App
