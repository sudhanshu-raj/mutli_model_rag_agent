import React, { useEffect, useRef, useState } from 'react';
import CheckIcon from "../../assets/check.png";
import ErrorIcon from "../../assets/close.png";
import { SVGIcon } from "../../component/fileIcons";

export function WaveAnimation({ 
  className = '', 
  style = {}, 
  paused = false,
  isUploadSuccess = true,
  colors = [
    'rgba(121, 40, 202, 0.9)',  // Base purple (#7928ca)
    'rgba(157, 58, 205, 0.9)',  // Purple-pink blend
    'rgba(193, 76, 208, 0.9)',  // Mid transition
    'rgba(229, 94, 211, 0.9)',  // Pink-purple blend
    'rgba(255, 112, 214, 0.9)', // Light pink blend
    'rgba(255, 0, 128, 0.9)',   // Base pink (#ff0080)
  ]
}) {
  const canvasRef = useRef(null);
  const [isPaused, setIsPaused] = useState(paused);
  const requestRef = useRef(null);

//   // Toggle pause function
//   const togglePause = () => {
//     const newPausedState = !isPaused;
//     setIsPaused(newPausedState);
    
//   };

  useEffect(() => {
    setIsPaused(paused);
  }, [paused]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const setCanvasSize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height || 150; // Default height if not specified
      }
    };
    
    setCanvasSize();
    window.addEventListener('resize', setCanvasSize);

    // Reduced number of waves for better clarity
    const waves = Array.from({ length: 4 }, (_, i) => ({
      amplitude: 12 + Math.random() * 15,  // Increased amplitude for more visible waves
      frequency: 0.05 + Math.random() * 0.05, // Adjusted for clearer wave patterns
      phase: Math.random() * Math.PI * 2,
      speed: 0.008 + Math.random() * 0.012, // Moderate speed for clear movement
      color: colors[Math.min(i, colors.length - 1)]
    }));

    let time = 0;
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Create a radial gradient background
      const bgGradient = ctx.createRadialGradient(
        canvas.width/2, canvas.height/2, 0,
        canvas.width/2, canvas.height/2, canvas.width/2
      );
      bgGradient.addColorStop(0, 'rgba(121, 40, 202, 0.7)');
      bgGradient.addColorStop(1, 'rgba(16, 25, 39, 0.5)');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw center point
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = Math.min(canvas.width, canvas.height) / 2;

      waves.forEach((wave, index) => {
        // Draw circular waves
        ctx.beginPath();
        
        // Make the base radius for each wave more distinct with better spacing
        const baseRadius = radius * (0.3 + 0.16 * index);
        
        // Draw a complete circle with more pronounced wave effects
        for (let angle = 0; angle <= Math.PI * 2; angle += 0.05) {
          // Calculate wave effect with increased amplitude
          const waveRadius = baseRadius + 
            Math.sin(angle * wave.frequency * 8 + wave.phase + time) * wave.amplitude +
            Math.sin(angle * wave.frequency * 12 + wave.phase + time * 1.5) * (wave.amplitude * 0.6);
          
          // Convert to cartesian coordinates
          const x = centerX + Math.cos(angle) * waveRadius;
          const y = centerY + Math.sin(angle) * waveRadius;

          if (angle === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        // Create a more distinct radial gradient for this wave
        const gradient = ctx.createRadialGradient(
          centerX, centerY, baseRadius - 20,
          centerX, centerY, baseRadius + 20
        );
        gradient.addColorStop(0, colors[index % colors.length]);
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.1)'); // Fade to transparent
        
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Add a subtle stroke to make waves more visible
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 0.5;
        ctx.stroke();

        // Only update phase when not paused
        if (!isPaused) {
          wave.phase += wave.speed;
        }
      });

      // Only update time when not paused
      if (!isPaused) {
        time += 0.02;
      }
      
      requestRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', setCanvasSize);
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [colors, isPaused]);

  return (
    <div 
      className={`${className}`}
      style={{
        position: 'relative',
        height: '200px', // Default height
        width: '200px',
        borderRadius: '50%',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...style
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          filter: 'brightness(1.1) contrast(1.2)',
          mixBlendMode: 'screen',
          borderRadius: 'inherit'
        }}
      />
      
      {/* Simple pause/play button */}
      <div 
        style={{ 
          position: 'absolute',
        //   display: 'flex',
        //   alignItems: 'center',
        //     justifyContent: 'center',
        //   top: '8px',
        //   right: '8px',
          backgroundColor: 'rgba(0,0,0,0.3)',
          borderRadius: '50%',
          width: '24px',
          height: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '12px',
          cursor: 'pointer',
          zIndex: 10
        }}
        // onClick={togglePause}
      >
        {isPaused ? (
           <>
         {isUploadSuccess ? (
      <>
       <SVGIcon type="success"/>
      </>
  ) : (
      <>
       <SVGIcon type="failed"/>
      </>
  )}
           </>

        ) : (
            <div className="animated-dots">
            <style>{`
              .animated-dots {
                display: flex;
                align-items: center;
                justify-content: center;
              }
              .dot {
                background: white;
                border-radius: 50%;
                width: 4px;
                height: 4px;
                margin: 0 2px;
                display: inline-block;
                animation: wave 1.5s infinite ease-in-out;
              }
              .dot:nth-child(2) {
                animation-delay: 0.2s;
              }
              .dot:nth-child(3) {
                animation-delay: 0.4s;
              }
              @keyframes wave {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
              }
            `}</style>
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
        
      </div>
    </div>
  );
}

export default WaveAnimation;