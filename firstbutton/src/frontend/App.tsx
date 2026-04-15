import { useState } from "react";
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
        onLanguageChange={setLanguage}
      />
    );
  }

  return (
    <DocumentCalendarWebsite language={language} onLanguageChange={setLanguage} onNavigateToAbout={() => setCurrentPage('about')} />
  );
}