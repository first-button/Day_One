import { useState } from "react";
import { motion } from "motion/react";
import { DocumentCalendarWebsite } from "./components/DocumentCalendarWebsite";
import { AboutUs } from "./components/AboutUs";

export default function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'about'>('home');
  const [language, setLanguage] = useState<'ko' | 'en'>('ko');

  if (currentPage === 'about') {
    return (
      <AboutUs 
        language={language}
        onBack={() => setCurrentPage('home')}
      />
    );
  }

  return (
    <div className="relative min-h-screen">
      {/* 메인 웹사이트: 접속 시 바로 노출되도록 변경 */}
      <DocumentCalendarWebsite language={language} onLanguageChange={setLanguage} onNavigateToAbout={() => setCurrentPage('about')} />

      {/* Floating Help Button: 애니메이션 효과 유지 */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        className="fixed bottom-6 right-6 z-40"
      >
      </motion.div>

      {/* Background Animation: 프로젝트의 미적 요소를 위해 유지 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {Array.from({ length: 20 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-blue-400/20 rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              scale: 0,
            }}
            animate={{
              y: [null, -100],
              scale: [0, 1, 0],
              opacity: [0, 0.6, 0],
            }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              delay: Math.random() * 2,
              ease: "easeOut",
            }}
          />
        ))}
      </div>
    </div>
  );
}