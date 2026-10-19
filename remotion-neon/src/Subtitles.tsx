import {interpolate, useCurrentFrame} from 'remotion';
import {COLORS, textGlow} from './theme';

export type Cue = {from: number; to: number; text: string};

// Phụ đề theo frame; fade in/out 6 frame
export const Subtitles: React.FC<{cues: Cue[]}> = ({cues}) => {
  const frame = useCurrentFrame();
  const cue = cues.find((c) => frame >= c.from && frame < c.to);
  if (!cue) return null;
  const opacity = interpolate(frame, [cue.from, cue.from + 6, cue.to - 6, cue.to], [0, 1, 1, 0]);
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 70,
        width: '100%',
        textAlign: 'center',
        fontFamily: 'Segoe UI, Arial, sans-serif',
        fontSize: 52,
        color: COLORS.text,
        textShadow: textGlow(COLORS.magenta),
        opacity,
      }}
    >
      <span style={{background: 'rgba(7,6,15,0.65)', padding: '8px 28px', borderRadius: 12}}>
        {cue.text}
      </span>
    </div>
  );
};
