import React from 'react';
import { Link } from '@tanstack/react-router';

interface FooterProps {
  className?: string;
}

export const Footer: React.FC<FooterProps> = ({ 
  className = ''
}) => {
  return (
    <footer className={`w-full py-6 px-4 border-t border-border/10 z-10 bg-background/50 backdrop-blur-sm ${className}`}>
      <div className="max-w-screen-xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-md bg-black outline outline-2 outline-white/10 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <span className="text-white font-bold text-sm">C</span>
          </div>
          <span className="text-sm text-foreground/60">© 2025 Cardify</span>
        </div>
        <nav className="flex items-center gap-6 text-xs text-foreground/60">
          <Link to="/" className="hover:text-foreground transition-colors">Quiz</Link>
          <Link to="/flashcards" className="hover:text-foreground transition-colors">Flash Cards</Link>
          <Link to="/" className="hover:text-foreground transition-colors">Lectures</Link>
          <Link to="/" className="hover:text-foreground transition-colors">Summaries</Link>
        </nav>
      </div>
    </footer>
  );
};

export default Footer;
