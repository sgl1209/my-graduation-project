// src/utils/tool.ts
export function throttle(fn: (...args: any[]) => void, delay = 300) {
  let timer: any = null;
  return (...args: any[]) => {
    if (!timer) {
      timer = setTimeout(() => {
        fn(...args);
        timer = null;
      }, delay);
    }
  };
}