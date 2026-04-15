import { Upload, Calendar, CheckCircle } from "lucide-react";

interface QuickGuideProps {
  language: 'ko' | 'en';
}

export function QuickGuide({ language }: QuickGuideProps) {
  const content = {
    ko: {
      steps: [
        {
          icon: Upload,
          title: "1. 파일 / 링크 업로드",
          description: "PDF, 이미지 파일을 클릭하거나 링크를 복사 및 붙여넣기 후, 원하는 색을 선택하여 업로드하세요."
        },
        {
          icon: Calendar,
          title: "2. AI 자동 인식",
          description: "AI가 자동으로 문서 속 일정을 인식하고 추출합니다. 평균 8초 소요!"
        },
        {
          icon: CheckCircle,
          title: "3. 캘린더에 저장",
          description: "인식된 일정이 로그인한 계정의 Google 캘린더에 추가됩니다."
        }
      ]
    },
    en: {
      steps: [
        {
          icon: Upload,
          title: "1. Upload File / Link",
          description: "Click to upload PDF/Image files or paste a link, and select a color."
        },
        {
          icon: Calendar,
          title: "2. AI Recognition",
          description: "AI automatically recognizes and extracts schedules from documents. Takes ~3 seconds!"
        },
        {
          icon: CheckCircle,
          title: "3. Save to Calendar",
          description: "Recognized schedules are automatically added to your Google Calendar."
        }
      ]
    }
  };

  const t = content[language];

  return (
    <div className="space-y-6">
      {t.steps.map((step, index) => {
        const Icon = step.icon;
        return (
          <div key={index} className="flex items-start space-x-4 p-4 bg-muted/50 rounded-lg">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0" style={{ marginRight: "16px" }}>
              <Icon className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-1">{step.title}</h3>
              <p className="text-muted-foreground">{step.description}</p>
            </div>
          </div>
        );
      })}

    </div>
  );
}