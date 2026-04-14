"""纯 NumPy 2D Perlin 噪声生成器。

用于地形自动生成的边界扰动和散点效果。
无外部依赖，全向量化运算。
"""

import numpy as np


def _fade(t: np.ndarray) -> np.ndarray:
    """Improved Perlin fade: 6t^5 - 15t^4 + 10t^3"""
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: np.ndarray, b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return a + t * (b - a)


def perlin_2d(
    shape: tuple[int, int],
    scale: float = 64.0,
    octaves: int = 4,
    persistence: float = 0.5,
    seed: int = 0,
    downsample: int = 0,
) -> np.ndarray:
    """生成 2D Perlin 噪声。

    Parameters
    ----------
    shape : (height, width)
    scale : 噪声尺度，越大越平滑
    octaves : 叠加层数
    persistence : 每层振幅衰减
    seed : 随机种子
    downsample : >0 时先在 1/downsample 分辨率生成再双线性插值放大（加速大图）

    Returns
    -------
    float32 array, shape=shape, 值域约 [-1, 1]
    """
    if downsample > 1:
        small_h = max(1, shape[0] // downsample)
        small_w = max(1, shape[1] // downsample)
        small = _perlin_multi((small_h, small_w), scale / downsample, octaves, persistence, seed)
        from scipy.ndimage import zoom
        result = zoom(small, (shape[0] / small_h, shape[1] / small_w), order=1)
        return result.astype(np.float32)

    return _perlin_multi(shape, scale, octaves, persistence, seed)


def _perlin_multi(
    shape: tuple[int, int],
    scale: float,
    octaves: int,
    persistence: float,
    seed: int,
) -> np.ndarray:
    """多层叠加 Perlin 噪声。"""
    result = np.zeros(shape, dtype=np.float32)
    amplitude = 1.0
    max_amplitude = 0.0

    for octave in range(octaves):
        freq = 2 ** octave
        oct_scale = scale / freq
        result += amplitude * _perlin_single(shape, oct_scale, seed + octave * 1000)
        max_amplitude += amplitude
        amplitude *= persistence

    result /= max_amplitude
    return result


def _perlin_single(
    shape: tuple[int, int],
    scale: float,
    seed: int,
) -> np.ndarray:
    """单层 Perlin 噪声（向量化）。"""
    h, w = shape
    rng = np.random.default_rng(seed)

    # 网格坐标
    grid_h = int(np.ceil(h / scale)) + 2
    grid_w = int(np.ceil(w / scale)) + 2

    # 随机梯度 (角度 → 单位向量)
    angles = rng.uniform(0, 2 * np.pi, (grid_h, grid_w)).astype(np.float32)
    grad_x = np.cos(angles)
    grad_y = np.sin(angles)

    # 像素坐标 → 网格内坐标
    ys = np.arange(h, dtype=np.float32) / scale
    xs = np.arange(w, dtype=np.float32) / scale

    # 网格整数坐标
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)

    # 小数部分
    dy = ys - y0.astype(np.float32)
    dx = xs - x0.astype(np.float32)

    # fade 曲线
    fy = _fade(dy)
    fx = _fade(dx)

    # 四个角的梯度点积 (向量化, 用广播)
    # shape: (h, w)
    y0_2d = y0[:, None]  # (h, 1)
    x0_2d = x0[None, :]  # (1, w)
    dy_2d = dy[:, None]  # (h, 1)
    dx_2d = dx[None, :]  # (1, w)

    def dot_grid(gy, gx):
        """计算梯度和距离向量的点积。"""
        return (grad_x[gy, gx] * dx_2d + grad_y[gy, gx] * dy_2d)

    # 限制索引范围
    y1 = np.minimum(y0 + 1, grid_h - 1)
    x1 = np.minimum(x0 + 1, grid_w - 1)

    y0_2d_arr = y0[:, None]
    y1_2d_arr = y1[:, None]
    x0_2d_arr = x0[None, :]
    x1_2d_arr = x1[None, :]

    # 四角点积 — 距离向量需要调整
    # 左上 (y0, x0): dist = (dy, dx)
    n00 = grad_x[y0_2d_arr, x0_2d_arr] * dx_2d + grad_y[y0_2d_arr, x0_2d_arr] * dy_2d
    # 右上 (y0, x1): dist = (dy, dx-1)
    n01 = grad_x[y0_2d_arr, x1_2d_arr] * (dx_2d - 1) + grad_y[y0_2d_arr, x1_2d_arr] * dy_2d
    # 左下 (y1, x0): dist = (dy-1, dx)
    n10 = grad_x[y1_2d_arr, x0_2d_arr] * dx_2d + grad_y[y1_2d_arr, x0_2d_arr] * (dy_2d - 1)
    # 右下 (y1, x1): dist = (dy-1, dx-1)
    n11 = grad_x[y1_2d_arr, x1_2d_arr] * (dx_2d - 1) + grad_y[y1_2d_arr, x1_2d_arr] * (dy_2d - 1)

    # 双线性插值
    fx_2d = fx[None, :]  # (1, w)
    fy_2d = fy[:, None]  # (h, 1)

    x_interp_0 = _lerp(n00, n01, fx_2d)
    x_interp_1 = _lerp(n10, n11, fx_2d)
    result = _lerp(x_interp_0, x_interp_1, fy_2d)

    return result
