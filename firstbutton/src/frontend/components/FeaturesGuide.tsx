import { ArrowLeft, Upload, FileText, Image as ImageIcon, Calendar, CheckCircle2, Sparkles, Clock, Bell } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import calendarImage from "../assets/calendar.jpg";

interface FeaturesGuideProps {
  onBack: () => void;
}

export function FeaturesGuide({ onBack }: FeaturesGuideProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={onBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              홈으로 돌아가기
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">W</span>
              </div>
              <span className="font-bold text-lg">첫단추</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-16 text-center">
        <div className="max-w-4xl mx-auto">
          <Badge className="mb-4 bg-orange-100 text-orange-700 hover:bg-orange-200">
            사용 가이드
          </Badge>
          <h1 className="text-4xl font-bold mb-4">
            첫단추 완벽 사용법
          </h1>
          <p className="text-lg text-muted-foreground">
            문서에서 캘린더까지, 3단계로 끝내는 일정 관리
          </p>
        </div>
      </section>

      {/* Step by Step Guide */}
      <section className="px-6 py-8">
        <div className="max-w-5xl mx-auto space-y-12">
          {/* Step 1 */}
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold">1</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold">문서 업로드</h2>
                  <p className="text-blue-100">
                    PDF, Word, 이미지 파일을 드래그하거나 선택하세요
                  </p>
                </div>
              </div>
            </div>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-bold mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    지원 파일 형식
                  </h3>
                  <ul className="space-y-2 text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span><strong>PDF 문서:</strong> 수업 계획서, 강의 일정표, 프로젝트 타임라인</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span><strong>Word 문서:</strong> .doc, .docx 형식의 일정 문서</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span><strong>이미지:</strong> 시간표 사진, 스크린샷 등 (.jpg, .png)</span>
                    </li>
                  </ul>
                </div>
                <div className="bg-muted rounded-lg p-6 flex items-center justify-center">
                  <div className="text-center">
                    <Upload className="w-16 h-16 text-blue-600 mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground">
                      파일을 여기에 드래그하거나<br />
                      클릭하여 선택하세요
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step 2 */}
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold">2</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold">AI 일정 인식</h2>
                  <p className="text-purple-100">
                    인공지능이 자동으로 날짜, 시간, 일정을 추출합니다
                  </p>
                </div>
              </div>
            </div>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-bold mb-3 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                    AI가 인식하는 정보
                  </h3>
                  <ul className="space-y-3 text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-purple-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Calendar className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <strong className="text-foreground">날짜</strong>
                        <p className="text-sm">2025년 10월 20일, 10/20, 20일 등 다양한 형식</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-purple-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Clock className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <strong className="text-foreground">시간</strong>
                        <p className="text-sm">14:00, 오후 2시, 2PM 등</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-purple-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                        <FileText className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <strong className="text-foreground">일정 내용</strong>
                        <p className="text-sm">수업명, 회의 주제, 과제 제목 등</p>
                      </div>
                    </li>
                  </ul>
                </div>
                <div className="bg-purple-50 rounded-lg p-6">
                  <h4 className="font-bold mb-3">예시</h4>
                  <div className="space-y-3">
                    <div className="bg-white p-3 rounded border-l-4 border-purple-500">
                      <p className="text-sm text-muted-foreground mb-1">문서 내용</p>
                      <p className="text-sm">"10월 25일 오후 3시 - 데이터베이스 중간고사"</p>
                    </div>
                    <div className="text-center py-2">
                      <Sparkles className="w-6 h-6 text-purple-600 mx-auto" />
                    </div>
                    <div className="bg-white p-3 rounded border-l-4 border-green-500">
                      <p className="text-sm text-muted-foreground mb-1">인식 결과</p>
                      <p className="text-sm"><strong>날짜:</strong> 2025-10-25</p>
                      <p className="text-sm"><strong>시간:</strong> 15:00</p>
                      <p className="text-sm"><strong>제목:</strong> 데이터베이스 중간고사</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step 3 */}
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-green-500 to-green-600 p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold">3</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold">캘린더 자동 연동</h2>
                  <p className="text-green-100">
                    Google 캘린더에 일정이 자동으로 추가됩니다
                  </p>
                </div>
              </div>
            </div>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-bold mb-3 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-green-600" />
                    자동 연동 기능
                  </h3>
                  <ul className="space-y-3 text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-foreground">일정 자동 생성</strong>
                        <p className="text-sm">인식된 모든 일정이 캘린더에 추가됩니다</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-foreground">알림 설정</strong>
                        <p className="text-sm">일정 30분 전 자동 알림</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-foreground">실시간 동기화</strong>
                        <p className="text-sm">모든 기기에서 즉시 확인 가능</p>
                      </div>
                    </li>
                  </ul>
                </div>
                <div className="bg-white rounded-lg overflow-hidden border">
                  <img
                    src={calendarImage}
                    alt="Google 캘린더 연동 예시"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Tips Section */}
      <section className="px-6 py-16 bg-gradient-to-br from-orange-50 to-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">💡 활용 팁</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  명확한 문서
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  날짜와 시간이 명확하게 표시된 문서일수록 인식률이 높아집니다. 표 형식이나 구조화된 문서를 권장합니다.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-purple-600" />
                  </div>
                  선명한 이미지
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  이미지 파일은 텍스트가 잘 보이도록 선명하게 촬영하거나 스크린샷으로 저장하세요.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <Bell className="w-5 h-5 text-green-600" />
                  </div>
                  알림 확인
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Google 캘린더 앱에서 알림을 허용하면 중요한 일정을 놓치지 않을 수 있습니다.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-16 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">지금 바로 시작해보세요</h2>
          <p className="text-lg text-muted-foreground mb-8">
            복잡한 일정 관리, 이제 첫단추로 간단하게 해결하세요
          </p>
          <Button
            size="lg"
            onClick={onBack}
            className="bg-orange-500 hover:bg-orange-600"
          >
            시작하기
          </Button>
        </div>
      </section>
    </div>
  );
}
