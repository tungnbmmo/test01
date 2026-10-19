import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, textGlow} from './theme';

// Chữ động: từng ký tự bay lên + sáng dần (neon)
export const AnimatedTitle: React.FC<{text: string; color?: string; top?: number; size?: number}> = ({
  text,
  color = COLORS.cyan,
  top = 760,
  size = 120,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        top,
        width: '100%',
        textAlign: 'center',
        fontFamily: 'Segoe UI, Arial, sans-serif',
        fontWeight: 800,
        fontSize: size,
        letterSpacing: 8,
        color: COLORS.text,
        textShadow: textGlow(color),
      }}
    >
      {text.split('').map((ch, i) => {
        const s = spring({frame: frame - i * 2, fps, config: {damping: 14}});
        const flicker = frame > i * 2 + 10 && frame < i * 2 + 16 ? 0.5 : 1;
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              whiteSpace: 'pre',
              opacity: interpolate(s, [0, 1], [0, 1]) * flicker,
              transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`,
            }}
          >
            {ch}
          </span>
        );
      })}
    </div>
  );
};
