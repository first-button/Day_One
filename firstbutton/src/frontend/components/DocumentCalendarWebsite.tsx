import { useState, useRef, useEffect } from "react";
import { Calendar, FileText, Image, Clock, CheckCircle, ArrowRight, Zap, HelpCircle, LogIn, X, Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { QuickGuide } from "./QuickGuide";
import { AnimatePresence, motion } from "motion/react"; // 애니메이션 효과
import { toast } from "sonner";
import calendarImage from "../assets/calendar.jpg";
import syllabusImage from "../assets/syllabus.jpg";
import photoTakingImage from "../assets/photo-taking.jpg";


interface DocumentCalendarWebsiteProps {
  onNavigateToGuide?: () => void;
  language: 'ko' | 'en';
  onLanguageChange?: (lang: 'ko' | 'en') => void;
  onNavigateToAbout?: () => void;
}

const translations = {
  ko: {
    title: "Day One",
    tagline: "Syllabus, Simplified",
    description: "PDF, Word, 이미지 속 일정을 AI가 자동으로 인식해서 Google 캘린더에 바로 추가해드립니다.",
    uploadButton: "파일 업로드하기",
    freeTrial: "공짜로 사용가능",
    noInstall: "설치 불필요",
    featuresTitle: "주요 기능",
    featuresSubtitle: "어떤 형태의 문서든 AI가 자동으로 일정을 찾아 캘린더에 추가합니다",
    pdfRecognition: "PDF 문서 인식",
    pdfDescription: "수업 계획서, 강의 일정표 등 PDF 속 모든 일정을 자동으로 추출합니다.",
    imageRecognition: "이미지 텍스트 인식",
    imageDescription: "사진으로 찍은 일정표나 화이트보드의 일정도 정확하게 인식합니다.",
    calendarSync: "자동 캘린더 연동",
    calendarDescription: "인식된 일정을 Google 캘린더에 자동으로 추가하고 알림까지 설정합니다.",
    ctaTitle: "지금 바로 Day One을 시작하세요",
    ctaSubtitle: "복잡한 일정 관리, 클릭 한번으로 끝내세요",
    aboutUs: "About Us",
    noCreditCard: "신용카드 불필요 • 언제든 취소 가능",
    upgradeToPremium: "프리미엄으로 업그레이드",
    login: "로그인",
    aiDisclaimer: "AI가 자동으로 일정을 인식하므로 중요한 일정은 반드시 확인해 주세요.",
  },
  en: {
    title: "Day One",
    tagline: "Syllabus, Simplified",
    description: "AI automatically recognizes schedules in PDFs, Word files, and images, and adds them directly to Google Calendar.",
    uploadButton: "Upload File",
    freeTrial: "Free to Use",
    noInstall: "No Installation Required",
    featuresTitle: "Key Features",
    featuresSubtitle: "AI automatically finds schedules in any document and adds them to your calendar",
    pdfRecognition: "PDF Document Recognition",
    pdfDescription: "Automatically extracts all schedules from course plans, lecture timetables, and more.",
    imageRecognition: "Image Text Recognition",
    imageDescription: "Accurately recognizes schedules from photographed timetables and whiteboards.",
    calendarSync: "Automatic Calendar Sync",
    calendarDescription: "Automatically adds recognized schedules to Google Calendar and sets reminders.",
    ctaTitle: "Start Using Day One Now",
    ctaSubtitle: "Manage complex schedules with just one click",
    aboutUs: "About Us",
    noCreditCard: "No credit card required • Cancel anytime",
    upgradeToPremium: "Upgrade to Premium",
    login: "Login",
    aiDisclaimer: "AI automatically recognizes schedules. Please verify important events.",
  }
};

// 파일 정보 타입 정의
interface SelectedFile {
  file: File;
  color: string;
}

export function DocumentCalendarWebsite({ language, onLanguageChange, onNavigateToAbout}: DocumentCalendarWebsiteProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [showQuickGuide, setShowQuickGuide] = useState(false);
  const t = translations[language];

  // 브라우저 쿠키에 user_email이 있는지 확인 (HttpOnly가 아닐 경우)
  // 가장 확실한 방법은 백엔드에 '상태 확인 API'를 하나 만드는 것이지만, 
  // 우선은 간단하게 '성공적으로 로그인 후 돌아왔을 때'를 가정해 처리합니다.
  useEffect(() => {
  const checkLogin = () => {
    const cookies = document.cookie.split('; ');
    const emailCookie = cookies.find(row => row.startsWith('user_email='));

    if (emailCookie) {
      // 쿠키 값 추출 및 디코딩
      const email = decodeURIComponent(emailCookie.split('=')[1]).replace(/"/g, '');
      const id = email.split('@')[0];
      
      setUserName(id);
      setIsLoggedIn(true);
      console.log("로그인 성공:", id);
    } else {
      setIsLoggedIn(false);
      setUserName("");
    }
  };

    checkLogin();
  }, []); // 페이지 로드 시 한 번만 실행

  

  const handleLogin = async () => {
    try {
      // 백엔드에서 구글 로그인 URL을 받아옵니다.
      const response = await fetch("/api/auth/login");
      const data = await response.json();
      
      // 구글 로그인 페이지로 이동 (리다이렉트)
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error("로그인 URL을 가져오는데 실패했습니다:", error);
      alert("서버와 통신할 수 없습니다.");
    }
  };

  // 1. 파일 선택 시 실행 (모달 열기)
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // 새로 선택된 파일들을 기존 목록에 추가하지 않고 새로 세팅 (원하면 추가 방식으로 변경 가능)
    const newFiles = Array.from(files).map(file => ({
      file,
      color: "1" // 기본 색상 1번
    }));

    setSelectedFiles(newFiles);
    setIsModalOpen(true); // 파일 선택 즉시 모달 띄우기
    
    // 같은 파일 재선택 가능하도록 input 초기화
    event.target.value = "";
  };

  // 2. 개별 파일 색상 변경 핸들러
  const handleColorChange = (index: number, newColor: string) => {
    setSelectedFiles(prev => prev.map((item, i) => 
      i === index ? { ...item, color: newColor } : item
    ));
  };

  // 3. 목록에서 파일 삭제 핸들러
  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => {
      const newFiles = prev.filter((_, i) => i !== index);
      if (newFiles.length === 0) setIsModalOpen(false); // 다 지우면 창 닫기
      return newFiles;
    });
  };

  // 4. "등록하기" 버튼 클릭 시 (백엔드 전송)
  // [Celery] 태스크 상태 polling
  const pollTaskStatus = async (taskId: string): Promise<{ status: string; count?: number; message?: string }> => {
    while (true) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const res = await fetch(`/api/schedule/upload/status/${taskId}`, {
        credentials: "include",
      });
      const data = await res.json();
      if (data.status !== "processing") return data;
    }
  };

  // [Celery] 비동기 업로드 — 즉시 task_id 받고 polling
  const handleFinalUpload = async () => {
    if (selectedFiles.length === 0) return;

    try {
      for (const item of selectedFiles) {
        const formData = new FormData();
        formData.append("uploaded_file", item.file);
        formData.append("event_color", item.color);

        const response = await fetch("/api/schedule/upload", {
          method: "POST",
          body: formData,
          credentials: "include",
        });

        if (response.status === 401) {
          alert("로그인이 필요합니다. 먼저 로그인해주세요!");
          return;
        }

        if (!response.ok) {
          throw new Error(`${item.file.name} 처리 실패`);
        }

        const { task_id } = await response.json();
        const result = await pollTaskStatus(task_id);

        if (result.status === "error") {
          throw new Error(result.message || `${item.file.name} 처리 실패`);
        }
      }

      alert("모든 일정이 성공적으로 등록되었습니다!");
      setIsModalOpen(false);
      setSelectedFiles([]);

    } catch (error) {
      console.error(error);
      alert("일부 파일 처리에 실패했습니다.");
    }
  };

  // [기존] 동기 업로드 — Celery 도입 전 코드
  // const handleFinalUpload = async () => {
  //   if (selectedFiles.length === 0) return;
  //
  //   try {
  //     alert(`${selectedFiles.length}개의 파일을 처리합니다...`);
  //
  //     for (const item of selectedFiles) {
  //       const formData = new FormData();
  //       formData.append("uploaded_file", item.file);
  //       formData.append("event_color", item.color);
  //
  //       const response = await fetch("/api/schedule/upload", {
  //         method: "POST",
  //         body: formData,
  //         credentials: "include",
  //       });
  //
  //       if (response.status === 401) {
  //         alert("로그인이 필요합니다. 먼저 로그인해주세요!");
  //         return;
  //       }
  //
  //       if (!response.ok) {
  //         throw new Error(`${item.file.name} 처리 실패`);
  //       }
  //     }
  //
  //     alert("모든 일정이 성공적으로 등록되었습니다!");
  //     setIsModalOpen(false);
  //     setSelectedFiles([]);
  //
  //   } catch (error) {
  //     console.error(error);
  //     alert("일부 파일 처리에 실패했습니다.");
  //   }
  // };

  const handleUploadClick = () => {
    if (!isLoggedIn) {
    alert("먼저 로그인을 해주세요!");
    handleLogin(); // 로그인창으로 바로 보냄
    return;
    }
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen bg-background relative">
      {/* Header */}
      <header className="border-b px-6 py-4 sticky top-0 z-50" style={{ backgroundColor: 'white' }}>
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full" />
            </div>
            <h1 className="text-2xl font-bold">{t.title}</h1>
          </div>

          <div className="flex items-center space-x-6">
            {/* Login / User Greeting */}
            {isLoggedIn ? (
              <div className="flex items-center">
                <span className="text-sm font-medium text-slate-700" style={{ marginRight: '16px' }}>
                  <strong className="text-orange-600">{userName}</strong>님, 안녕하세요!
                </span>
                <Button
                  variant="outline"
                  className="gap-2"
                  style={{ marginRight: '16px' }}
                  onClick={() => {
                    document.cookie = "user_email=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    window.location.reload();
                  }}
                >
                  Sign Out
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                className="gap-2"
                style={{ marginRight: '16px' }}
                onClick={handleLogin}
              >
                <LogIn className="h-4 w-4" />
                {t.login}
              </Button>
            )}

            {/* Language Selector */}
            <div className="flex items-center space-x-1 bg-muted rounded-lg" style={{ padding: '6px' }}>
              <Button
                variant={language === 'ko' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onLanguageChange?.('ko')}
                className="h-8 px-3"
              >
                한국어
              </Button>
              <Button
                variant={language === 'en' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onLanguageChange?.('en')}
                className="h-8 px-3"
              >
                English
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section 
        className="px-6 py-16"
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <Badge className="bg-orange-100 text-orange-800 border-orange-200">
                  <Zap className="w-3 h-3 mr-1" />
                  AI {language === 'ko' ? '문서 인식' : 'Document Recognition'}
                </Badge>
                <h1 className="text-4xl lg:text-5xl font-bold leading-tight">
                  {t.tagline}
                </h1>
                <p className="text-xl text-muted-foreground">
                  {t.description}
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <input 
                  type="file" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  style={{ display: 'none' }} 
                  accept=".jpg,.jpeg,.png,.pdf"
                  multiple // 여러 파일 선택 가능하게 변경
                />

                <Button
                  size="lg"
                  className="bg-orange-500 hover:bg-orange-600"
                  data-tutorial="start"
                  onClick={handleUploadClick}
                >
                  {t.uploadButton}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>

              <div className="flex items-center space-x-8 text-sm text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{t.freeTrial}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{t.noInstall}</span>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="relative aspect-square rounded-2xl overflow-hidden bg-gradient-to-br from-orange-100 to-orange-50">
                <img
                  src={calendarImage}
                  alt="문서 및 캘린더"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-16 bg-muted/30">
        <div className="max-w-7xl mx-auto">
           <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">{t.featuresTitle}</h2>
            <p className="text-lg text-muted-foreground">
              {t.featuresSubtitle}
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="relative overflow-hidden">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle>{t.pdfRecognition}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {t.pdfDescription}
                </p>
                <div className="aspect-video bg-muted rounded-lg overflow-hidden">
                  <img
                    src={syllabusImage}
                    alt="Syllabus preview"
                    className="w-full h-full object-cover"
                  />
                </div>
              </CardContent>
            </Card>
            <Card className="relative overflow-hidden">
              <CardHeader>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <Image className="w-6 h-6 text-green-600" />
                </div>
                <CardTitle>{t.imageRecognition}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {t.imageDescription}
                </p>
                <div className="aspect-video bg-muted rounded-lg overflow-hidden">
                  <img src={photoTakingImage} alt="Photo taking preview" className="w-full h-full object-cover"/>
                </div>
              </CardContent>
            </Card>
            <Card className="relative overflow-hidden">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Calendar className="w-6 h-6 text-purple-600" />
                </div>
                <CardTitle>{t.calendarSync}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {t.calendarDescription}
                </p>
                <div className="aspect-video bg-white rounded-lg overflow-hidden flex items-center justify-center p-4">
                  <img src={calendarImage} alt="Calendar" className="w-full h-full object-contain" />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-16 bg-gradient-to-br from-orange-500 to-red-500">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            {t.ctaTitle}
          </h2>
          <p className="text-xl mb-8 text-white/90">
            {t.ctaSubtitle}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="secondary"
              size="lg"
              style={{ backgroundColor: 'white', color: '#f97316', fontWeight: 600 }}
            >
              {t.upgradeToPremium}
            </Button>
            <Button
              variant="secondary"
              size="lg"
              style={{ backgroundColor: 'white', color: '#f97316', fontWeight: 600 }}
              onClick={onNavigateToAbout}
            >
              {t.aboutUs}
            </Button>
          </div>
          <p style={{ marginTop: '40px' }} className="text-sm text-white/75">
            {t.noCreditCard}
          </p>
        </div>
      </section>

      {/* AI Disclaimer Footer */}
      <footer className="px-6 py-4 border-t bg-muted/30">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-xs text-muted-foreground">
            {t.aiDisclaimer}
          </p>
        </div>
      </footer>

      {/* 5. 파일 선택 확인 모달 (AnimatePresence로 부드럽게) */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
            >
              {/* 모달 헤더 */}
              <div className="bg-orange-500 p-4 flex justify-between items-center text-white">
                <h3 className="font-bold text-lg flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  선택된 파일 목록
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="hover:bg-orange-600 p-1 rounded-full transition">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* 파일 리스트 영역 */}
              <div className="p-6 max-h-[60vh] overflow-y-auto space-y-4">
                {selectedFiles.map((item, index) => (
                  <div key={index} className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-200 shadow-sm">
                    {/* 왼쪽: 파일 정보 */}
                    <div className="flex items-center space-x-3 overflow-hidden">
                      <div className="w-10 h-10 bg-white rounded-lg border flex items-center justify-center shrink-0">
                        {item.file.name.endsWith('.pdf') ? (
                          <FileText className="text-red-500 w-6 h-6" />
                        ) : (
                          <Image className="text-blue-500 w-6 h-6" />
                        )}
                      </div>
                      <div className="truncate">
                        <p className="font-medium text-sm truncate max-w-[150px]" title={item.file.name}>
                          {item.file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {(item.file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>

                    {/* 오른쪽: 색상 선택 및 삭제 버튼 */}
                    <div className="flex items-center space-x-2 shrink-0">
                      <select
                        value={item.color}
                        onChange={(e) => handleColorChange(index, e.target.value)}
                        className="text-sm border rounded px-2 py-1 bg-white focus:ring-2 focus:ring-orange-500 outline-none cursor-pointer"
                        title="캘린더 색상"
                      >
                         {Array.from({ length: 11 }, (_, i) => i + 1).map((num) => (
                          <option key={num} value={num}>Color {num}</option>
                        ))}
                      </select>
                      
                      <button 
                        onClick={() => handleRemoveFile(index)}
                        className="text-slate-400 hover:text-red-500 transition p-1"
                        title="파일 삭제"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* 모달 하단 버튼 */}
              <div className="p-4 border-t bg-slate-50 flex justify-end space-x-3">
                <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
                  취소
                </Button>
                <Button className="bg-orange-500 hover:bg-orange-600" onClick={handleFinalUpload}>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  일정 등록하기
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Quick Guide Modal */}
      {showQuickGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowQuickGuide(false)}
          />
          <div className="relative bg-background rounded-lg border shadow-lg w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowQuickGuide(false)}
              className="absolute top-4 right-4 opacity-70 hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
              <span className="sr-only">Close</span>
            </button>
            <div className="flex flex-col gap-2 mb-4">
              <h2 className="text-lg font-semibold flex items-center space-x-2">
                <HelpCircle className="w-5 h-5 text-blue-500" />
                <span>{language === 'ko' ? '빠른 가이드' : 'Quick Guide'}</span>
              </h2>
              <p className="text-muted-foreground text-sm">
                {language === 'ko'
                  ? 'Day One을 사용하는 방법을 배워보세요!'
                  : 'Learn how to use Day One!'}
              </p>
            </div>
            <div className="space-y-4 py-4">
              <QuickGuide language={language} />
            </div>
          </div>
        </div>
      )}

      {/* Floating Quick Guide Button */}
      <div className="fixed bottom-6 left-6 flex flex-col gap-3 z-40">
        <Button
          size="lg"
          onClick={() => setShowQuickGuide(true)}
          className="rounded-full shadow-lg hover:shadow-xl transition-shadow bg-blue-500 hover:bg-blue-600"
        >
          <HelpCircle className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}
