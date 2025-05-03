import React, { useEffect, useRef, useState } from 'react';

export function WaveAnimation({ 
  className = '', 
  style = {}, 
  paused = false,
  onTogglePause = null,
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

  // Toggle pause function
  const togglePause = () => {
    const newPausedState = !isPaused;
    setIsPaused(newPausedState);
    if (onTogglePause) onTogglePause(newPausedState);
  };

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

    // Wave parameters
    const waves = Array.from({ length: colors.length }, (_, i) => ({
      amplitude: 15 + Math.random() * 15,
      frequency: 0.0015 + Math.random() * 0.002,
      phase: Math.random() * Math.PI * 2,
      speed: 0.002 + Math.random() * 0.002,
      y: canvas.height * (i / colors.length),
      color: colors[i]
    }));

    let time = 0;
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = 'rgba(16, 25, 39, 0.5)'; // Dark background
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      waves.forEach((wave) => {
        ctx.beginPath();
        
        for (let x = 0; x <= canvas.width; x += 2) {
          const y = wave.y + 
            Math.sin(x * wave.frequency + wave.phase + time) * wave.amplitude +
            Math.sin(x * wave.frequency * 1.5 + wave.phase + time * 1.2) * (wave.amplitude * 0.4);

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        const gradient = ctx.createLinearGradient(0, wave.y - wave.amplitude, 0, wave.y + wave.amplitude);
        gradient.addColorStop(0, wave.color);
        const nextColorIndex = Math.min(colors.length - 1, colors.indexOf(wave.color) + 1);
        gradient.addColorStop(1, colors[nextColorIndex]);
        
        ctx.lineTo(canvas.width, canvas.height);
        ctx.lineTo(0, canvas.height);
        ctx.closePath();
        
        ctx.fillStyle = gradient;
        ctx.fill();

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
        height: '150px', // Default height
        width: '100%',
        borderRadius: '10px',
        overflow: 'hidden',
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
          top: '8px',
          right: '8px',
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
        onClick={togglePause}
      >
        {isPaused ? '▶' : '❚❚'}
      </div>
    </div>
  );
}

export default WaveAnimation;