import { Monitor, ShieldAlert } from 'lucide-react'

function App() {
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

                {/* Quick Guide */}
                <div className="p-6 bg-amber-50 rounded-2xl border border-amber-100 text-left animate-fade-in-up delay-300">
                    <div className="flex items-center gap-2 text-amber-700 font-bold mb-3">
                        <ShieldAlert size={20} />
                        <span>macOS 실행 가이드</span>
                    </div>
                    <p className="text-sm text-amber-800 leading-relaxed">
                        처음 실행 시 "확인할 수 없는 개발자" 경고가 뜨면 <strong>[시스템 설정] &gt; [개인정보 보호 및 보안]</strong> 하단에서 **[확인 없이 열기]**를 눌러주세요.
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
