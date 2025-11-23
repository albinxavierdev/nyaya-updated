// // page.tsx
// 'use client';

// import { Button } from '@/components/ui/button';
// import Image from 'next/image';
// import { useTheme } from 'next-themes';
// import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
// import { Suspense, useState } from 'react';
// import { useRouter } from 'next/navigation';
// import Loading from '@/components/loading';
// import { useAuth } from '@/app/authProvider';
// import Ripple from '@/components/magicui/ripple';
// import AnimatedGradientText from '@/components/magicui/animated-gradient-text';
// import { cn } from '@/lib/utils';
// import { ChevronRight } from 'lucide-react';
// import HyperText from '@/components/magicui/hyper-text';
// import GradualSpacing from '@/components/magicui/gradual-spacing';

// function HomeContent() {
//   const { theme, setTheme } = useTheme();
//   const [inputValue, setInputValue] = useState('');
//   const { isAuthenticated } = useAuth();
//   const router = useRouter();

//   const placeholders = [
//     'Hello there how are you doing',
//     'Tell me more about ...',
//   ];

//   const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     setInputValue(e.target.value);
//   };

//   const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
//     e.preventDefault();

//     setTimeout(() => {
//       if (isAuthenticated) {
//         router.push(`/chat?query=${encodeURIComponent(inputValue)}`);
//       } else {
//         router.push(`/signin`);
//       }
//     }, 1500);
//   };

//   return (
//     <div className="h-full flex flex-col justify-center items-center relative">
//       <Ripple />
//       <div className="z-10 flex  items-center justify-center p-2">
//       <div className="w-full md:w-[60%] p-4">
//         <PlaceholdersAndVanishInput
//           placeholders={placeholders}
//           onChange={handleChange}
//           onSubmit={onSubmit}
//           value={inputValue}
//           setValue={setInputValue}
//         />
//       </div>
//     </div>
//   );
// }

// export default function Home() {
//   return (
//     <Suspense fallback={<Loading />}>
//       <HomeContent />
//     </Suspense>
//   );
// }

// 'use client';

// import { Button } from '@/components/ui/button';
// import Image from 'next/image';
// import { useTheme } from 'next-themes';
// import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
// import { Suspense, useState } from 'react';
// import { useRouter } from 'next/navigation';
// import Loading from '@/components/loading';
// import { useAuth } from '@/app/authProvider';
// import Ripple from '@/components/magicui/ripple';
// import AnimatedGradientText from '@/components/magicui/animated-gradient-text';
// import { cn } from '@/lib/utils';
// import { ChevronRight } from 'lucide-react';
// import HyperText from '@/components/magicui/hyper-text';
// import GradualSpacing from '@/components/magicui/gradual-spacing';

// function HomeContent() {
//   const { theme, setTheme } = useTheme();
//   const [inputValue, setInputValue] = useState('');
//   const { isAuthenticated } = useAuth();
//   const router = useRouter();

//   const placeholders = [
//     'Hello there how are you doing',
//     'Tell me more about ...',
//   ];

//   const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     setInputValue(e.target.value);
//   };

//   const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
//     e.preventDefault();

//     setTimeout(() => {
//       if (isAuthenticated) {
//         router.push(`/chat?query=${encodeURIComponent(inputValue)}`);
//       } else {
//         router.push(`/signin`);
//       }
//     }, 1500);
//   };

//   return (
//     <div className="h-full flex flex-col justify-center items-center relative">
//       <Ripple />
//       <div className="z-10 flex items-center justify-center p-2 ">
//         <AnimatedGradientText>

//       <div className="w-full md:w-[70%] p-4">
//         <PlaceholdersAndVanishInput
//           placeholders={placeholders}
//           onChange={handleChange}
//           onSubmit={onSubmit}
//           value={inputValue}
//           setValue={setInputValue}
//         />
//       </div>
//     </div>
//   );
// }

// export default function Home() {
//   return (
//     <Suspense fallback={<Loading />}>
//       <HomeContent />
//     </Suspense>
//   );
// }

'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/authProvider';
import Ripple from '@/components/magicui/ripple';

function HomeContent() {
  const [inputValue, setInputValue] = useState('');
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [isAnimating, setIsAnimating] = useState(false);

  const placeholders = [
    'Hello there how are you doing',
    'Tell me more about ...',
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsAnimating(true);

    setTimeout(() => {
      if (isAuthenticated) {
        router.push(`/chat?query=${encodeURIComponent(inputValue)}`);
      } else {
        router.push(`/signin`);
      }
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col justify-center items-center relative">
      <Ripple />
      
      {/* Logo Section */}
      <div className="z-10 mb-8 flex flex-col items-center">
        <Image
          src="/logo-black.png"
          alt="Nyayantar AI Logo"
          width={120}
          height={120}
          className="h-24 w-24 mb-4"
          priority
        />
        <h1 className="text-4xl md:text-6xl font-bold text-center mb-2">
          Nyayantar AI
        </h1>
        <p className="text-lg text-muted-foreground text-center max-w-md">
          Your Legal Guide, Powered by AI
        </p>
      </div>
      
      <div
        className={`w-full md:w-[70%] p-4 transition-all duration-1500 ${
          isAnimating ? 'md:translate-y-24 lg:md:translate-y-36' : ''
        }`}
      >
        <PlaceholdersAndVanishInput
          placeholders={placeholders}
          onChange={handleChange}
          onSubmit={onSubmit}
          value={inputValue}
          setValue={setInputValue}
        />
      </div>
    </div>
  );
}

export default HomeContent;
