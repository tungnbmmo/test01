import {random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, glow} from '../theme';
import {Fade, MONO, Svg, clamp01} from './common';

const STARS = Array.from({length: 90}).map((_, i) => ({
  x: random(`sx${i}`) * 1920,
  y: random(`sy${i}`) * 700,
  r: 1 + random(`sr${i}`) * 2.2,
  p: random(`sp${i}`) * 6,
}));

const SRC = {x: 1060, y: 140};

// Kính thiên văn vô tuyến quay lên trời, nhận tín hiệu từ một điểm xa
export const Telescope: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tilt = 35 * spring({frame, fps, config: {damping: 200}, durationInFrames: 50});
  const ping = clamp01(frame, 60, 70);

  return (
    <Fade>
      <Svg>
        {STARS.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill={COLORS.text} opacity={0.35 + 0.45 * Math.sin(frame / 15 + s.p)} />
        ))}

        {/* tín hiệu lan từ nguồn về phía đĩa */}
        <g style={{opacity: ping}}>
          {[0, 1, 2].map((k) => {
            const t = ((frame + k * 30) % 90) / 90;
            return (
              <circle key={k} cx={SRC.x} cy={SRC.y} r={t * 720} fill="none" stroke={COLORS.lime} strokeWidth={4} opacity={1 - t} style={{filter: glow(COLORS.lime, 0.6)}} />
            );
          })}
          <circle cx={SRC.x} cy={SRC.y} r={10 + 3 * Math.sin(frame / 4)} fill={COLORS.lime} style={{filter: glow(COLORS.lime)}} />
        </g>

        <line x1="0" x2="1920" y1="830" y2="830" stroke={COLORS.magenta} strokeWidth="3" style={{filter: glow(COLORS.magenta, 0.5)}} />

        <g transform="translate(700 830)" style={{filter: glow(COLORS.cyan, 0.7)}} stroke={COLORS.cyan} strokeWidth="6" fill="none" strokeLinejoin="round" strokeLinecap="round">
          <path d="M -50 0 L -18 -180 L 18 -180 L 50 0 Z" />
          <line x1="-34" y1="-90" x2="34" y2="-90" />
          <g transform={`translate(0 -190) rotate(${tilt})`}>
            <path d="M -230 -20 Q 0 140 230 -20 Z" />
            <line x1="0" y1="45" x2="0" y2="-150" />
            <circle cx="0" cy="-150" r="12" fill={COLORS.cyan} />
            {frame > 60 && (
              <circle cx="0" cy="-150" r={14 + ((frame - 60) % 30) * 1.6} stroke={COLORS.magenta} opacity={1 - ((frame - 60) % 30) / 30} />
            )}
          </g>
        </g>

        {frame > 90 && (
          <text x="1260" y="300" fontFamily={MONO} fontSize="40" fill={COLORS.lime} opacity={frame % 40 < 28 ? 1 : 0.3} style={{filter: glow(COLORS.lime, 0.4)}}>
            ◉ SIGNAL DETECTED
          </text>
        )}
      </Svg>
    </Fade>
  );
};
