import { ArrowLeft } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

interface AboutUsProps {
  language: 'ko' | 'en';
  onBack: () => void;
}

const teamMembers = [
  {
    name: "문원재",
    nameEn: "Wonjae Moon",
    role: "디자이너",
    roleEn: "Designer",
    description: "사용자 경험을 최우선으로 생각하는 디자이너입니다.",
    descriptionEn: "A designer who prioritizes user experience above all.",
    avatar: "🎨",
  },
  {
    name: "전호찬",
    nameEn: "Hochan Jeon",
    role: "개발자",
    roleEn: "Developer",
    description: "효율적인 코드로 최고의 성능을 구현합니다.",
    descriptionEn: "Implements optimal performance with efficient code.",
    avatar: "💻",
  },
  {
    name: "전상현",
    nameEn: "Sanghyun Jeon",
    role: "개발자",
    roleEn: "Developer",
    description: "안정적이고 확장 가능한 시스템을 만듭니다.",
    descriptionEn: "Builds stable and scalable systems.",
    avatar: "⚡",
  },
];

export function AboutUs({ language, onBack }: AboutUsProps) {
  const t = {
    ko: {
      title: "About Us",
      subtitle: "Day One을 만드는 사람들",
      mission: "우리의 미션",
      missionText: "복잡한 일정 관리를 단순하게 만들어, 모든 사람이 시간을 더 효율적으로 사용할 수 있도록 돕습니다.",
      team: "팀 소개",
      backToHome: "홈으로 돌아가기",
      vision: "우리의 비전",
      visionText: "AI 기술을 활용하여 일정 관리의 미래를 만들어갑니다. 누구나 쉽게 사용할 수 있는 도구로 생산성을 극대화하는 것이 우리의 목표입니다.",
    },
    en: {
      title: "About Us",
      subtitle: "The people behind Day One",
      mission: "Our Mission",
      missionText: "We simplify complex schedule management to help everyone use their time more efficiently.",
      team: "Meet the Team",
      backToHome: "Back to Home",
      vision: "Our Vision",
      visionText: "We're shaping the future of schedule management with AI technology. Our goal is to maximize productivity with tools that anyone can use easily.",
    }
  };

  const content = t[language];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b px-6 py-4 sticky top-0 z-50" style={{ backgroundColor: 'white' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Button variant="ghost" onClick={onBack} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            {content.backToHome}
          </Button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full" />
            </div>
            <h1 className="text-2xl font-bold">Day One</h1>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-16 bg-gradient-to-br from-orange-50 to-red-50">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="font-bold mb-4" style={{ fontSize: '50px' }}>{content.title}</h1>
          <p className="text-xl text-muted-foreground">{content.subtitle}</p>
        </div>
      </section>

      {/* Mission & Vision Section */}
      <section className="px-6 py-16">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-8">
          <Card className="border" style={{ padding: '40px' }}>
            <div className="text-center">
              <h2 className="text-3xl font-bold mb-4">{content.mission}</h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                {content.missionText}
              </p>
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0" style={{ padding: '40px' }}>
            <div className="text-center">
              <h3 className="text-3xl font-bold mb-4">{content.vision}</h3>
              <p className="text-lg text-white/90 leading-relaxed">
                {content.visionText}
              </p>
            </div>
          </Card>
        </div>
      </section>

      {/* Team Section */}
      <section className="px-6 py-16 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">{content.team}</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {teamMembers.map((member, index) => (
              <Card key={index} className="overflow-hidden hover:shadow-xl transition-shadow">
                <CardContent className="text-center" style={{ padding: '40px' }}>
                  <div className="mx-auto mb-6 bg-orange-500 rounded-full flex items-center justify-center" style={{ width: '100px', height: '100px' }}>
                    <span style={{ fontSize: '40px' }}>{member.avatar}</span>
                  </div>
                  <h3 className="text-2xl font-bold mb-1">
                    {language === 'ko' ? member.name : member.nameEn}
                  </h3>
                  <p className="text-orange-500 font-semibold mb-4">
                    {language === 'ko' ? member.role : member.roleEn}
                  </p>
                  <p className="text-muted-foreground leading-relaxed">
                    {language === 'ko' ? member.description : member.descriptionEn}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 border-t" style={{ paddingTop: '50px', paddingBottom: '40px' }}>
        <div className="max-w-4xl mx-auto text-center text-muted-foreground">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full" />
            </div>
            <span className="font-bold text-foreground">Day One</span>
          </div>
          <p className="text-sm">
            © 2026 Day One. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
