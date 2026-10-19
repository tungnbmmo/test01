export const COLORS = {
  bg: '#07060f',
  cyan: '#00f0ff',
  magenta: '#ff2bd6',
  lime: '#b6ff3b',
  text: '#eaf6ff',
};

export const glow = (color: string, size = 1) =>
  `drop-shadow(0 0 ${6 * size}px ${color}) drop-shadow(0 0 ${18 * size}px ${color}) drop-shadow(0 0 ${40 * size}px ${color})`;

export const textGlow = (color: string) =>
  `0 0 6px ${color}, 0 0 18px ${color}, 0 0 42px ${color}`;
