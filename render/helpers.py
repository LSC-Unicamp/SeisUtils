import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def MergeObj(dict_1, dict_2):
    result = dict_1 | dict_2
    return result


def data2numpy(filepath, n1, n2, n3):
    with open(filepath, mode='rb') as f:
        data = np.fromfile(f, dtype=np.float32)
        if not n3:
            return np.reshape(data, [n1, n2])
        else:
            return np.reshape(data, [n3, n2, n1], order='C')


def psnr(baseline, comparison):
    mse = np.mean((baseline - comparison) ** 2)
    if mse == 0:
        raise ValueError('Oops, MSE == 0')

    if np.isinf(mse):
        return 0, 0

    max_pixel = np.max(comparison)
    psnr_val = 20 * np.log10(max_pixel / np.sqrt(mse))

    mre = np.mean(np.abs(baseline - comparison)) / np.mean(np.abs(baseline))

    return float(psnr_val), float(mse), float(mre)

def _ssim(a, b):
    from skimage.metrics import structural_similarity as ssim
    if a.shape != b.shape:
        raise ValueError("Error: Images must have the same dimensions.")

    # Determine the data range dynamically
    data_range = a.max() - a.min()
    
    # Compute SSIM for each slice along the depth dimension
    ssim_scores = [
        ssim(a[i], b[i], data_range=data_range) for i in range(a.shape[0])
    ]

    return np.mean(ssim_scores)  # Return the average SSIM over all slices


def clip_perc(frame, perc):
    clip = np.percentile(frame.copy().reshape(-1), perc)
    return np.clip(frame, -clip, +clip)


def plot_image(frame, d2=1, d3=1, vmin=None, vmax=None, colorbar=False, img_name='plot',
               cmap=plt.cm.gray, save=False, d1=None, ax=None, dpi=200, formats=('png',), top=0):
    """Plot a depth section: rows = depth (n1, spacing d1), columns = distance (spacing d2).

    d3 is kept for backward compatibility: it was used as the depth spacing when d1 is
    not given. With `ax`, draws on that axis (used by the cineloop) and never saves.
    With `save`, writes <img_name>.<fmt> for each format and closes the figure.
    `top` is the depth (m) of the first row, e.g. after crop_depth.
    """
    if d1 is None:
        d1 = d3
    x_max = (frame.shape[1] * d2) / 1000  # distance, in km
    y_top = top / 1000                                # depth of the first row, in km
    y_max = y_top + (frame.shape[0] * d1) / 1000      # depth of the last row, in km

    own_figure = ax is None
    if own_figure:
        fig, ax = plt.subplots()

    # extent (left, right, bottom, top): the shallowest row at the top (origin='upper')
    im = ax.imshow(frame, extent=[0, x_max, y_max, y_top], cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_ylabel('Depth (km)')
    ax.set_xlabel('Distance (km)')

    if colorbar:
        ax.figure.colorbar(im, ax=ax)

    if own_figure:
        if save:
            for fmt in formats:
                fig.savefig(f'{img_name}.{fmt}', bbox_inches='tight', dpi=dpi, format=fmt)
            print('  wrote', ', '.join(f'{img_name}.{fmt}' for fmt in formats))
        plt.close(fig)


def border_detector(frame):
    import cv2
    return cv2.Laplacian(frame, ddepth=cv2.CV_32F, ksize=3)


def blur(frame):
    import cv2
    return cv2.GaussianBlur(frame, (5, 5), 0)


def crop_depth(frame, crop_meters, d1):
    """Drop the first crop_meters of depth (rows, spacing d1).

    The cropped section starts at depth cropped_top(crop_meters, d1); pass it as
    plot_image(top=...) so the depth axis keeps the true depths.
    """
    return frame.copy()[int(crop_meters/d1):, :]


def cropped_top(crop_meters, d1):
    """Depth (m) of the first row left by crop_depth."""
    return int(crop_meters/d1) * d1


def render_cineloop(a, d2, d3):
    playing = True
    num_frames = a.shape[0]
    fig, ax = plt.subplots()
    frame_num = 0

    def update(animation_framenum):
        nonlocal frame_num

        # Calculate the frame number with backward motion
        frame_idx = animation_framenum if playing else frame_num % (2 * num_frames)
        if frame_idx >= num_frames:
            frame_num = 2 * num_frames - 1 - frame_idx  # Go backward in time
        else:
            frame_num = frame_idx  # Go forward in time

        plt.clf()

        print(f'Frame {frame_num}/{num_frames}')
        frame = clip_perc(a[frame_num, :, :,].T, 99.5)
        plot_image(frame, d2, d3, ax=plt.gca())

        plt.title(f'Frame {frame_num}/{num_frames}')

    ani = FuncAnimation(fig, update, frames=num_frames * 2, interval=50,)

    def on_close(event):
        import sys
        print("Window closed. Exiting the script.")
        sys.exit()

    def start_animation(event):
        nonlocal playing
        playing = True
        ani.resume()

    def pause_animation(event):
        nonlocal playing
        playing = False
        ani.pause()

    def next_frame(event):
        nonlocal playing
        nonlocal frame_num
        playing = False
        ani.resume()
        frame_num = frame_num + 1

    def prev_frame(event):
        nonlocal playing
        nonlocal frame_num
        playing = False
        ani.resume()
        frame_num = frame_num - 1


    fig.canvas.mpl_connect('close_event', on_close)
    plt.rcParams['keymap.save'].remove('s')
    fig.canvas.mpl_connect('key_press_event', lambda event: start_animation(event) if event.key == 'c' else None)
    fig.canvas.mpl_connect('key_press_event', lambda event: pause_animation(event) if event.key == 's' else None)
    fig.canvas.mpl_connect('key_press_event', lambda event: next_frame(event) if event.key == 'right' else None)
    fig.canvas.mpl_connect('key_press_event', lambda event: prev_frame(event) if event.key == 'left' else None)

    try:
        plt.show()
    except KeyboardInterrupt:
        ani.event_source.stop()
        print("\nAnimation stopped by user.")
