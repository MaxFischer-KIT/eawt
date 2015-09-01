
# standard library imports
import time
import math

# third party imports

# application/library imports


_prefix_1000 = {
    -4: "p",
    -3: "n",
    -2: "u",
    -1: "m",
    0: "",
    1: "k",
    2: "M",
    3: "G",
    4: "T",
    5: "P",
    6: "E",
    7: "Z",
    8: "Y",
}


def numeric_prefix(numeric, pow2=False):
    """
    Convert a number to a shortened version using SI prefixes

    Shortens numbers using SI prefixes. For example, ``899812`` is converted to
    ``899k``. The returned representation is always between 1 and 4 characters
    long.

    :param numeric:
    :param pow2:
    :return:
    """
    if numeric == 0:
        return "0"
    base = pow2 and 1024 or 1000
    exp3 = int(math.log(numeric, base)) if numeric >=1 else int(math.log(numeric, base))-1
    if exp3 > 8:
        exp3 = 8
    elif exp3 < -4:
        exp3 = -4
    num_red = numeric * (base ** -exp3)
    if exp3 == 0:
        if num_red < 9.99500000001:
            return "%.2f" % (num_red)
        if num_red < 99.95:
            return "%.1f" % (num_red)
    if num_red < 9.9500000001:
        return "%.1f%s" % (num_red,_prefix_1000[exp3])
    return "%.0f%s" % (num_red,_prefix_1000[exp3])


def nice_bytes(numbytes, pow2 = False):
    """Convert a byte size to human readable format"""
    if pow2:
        return numeric_prefix(numbytes, pow2=True) + "iB"
    return numeric_prefix(numbytes, pow2=False) + "B"


class Progress(object):
    """
    Progress tracker and indicator

    Implements a progress counter as well as a progress indicator. Progress may
    be advanced by calling :py:meth:`Progress.step` or :py:meth:`Progress.add`.
    Every ``steps``, the tracker automatically outputs a progress bar in the
    style ``Progress: [=>..17%...]``.

    :param maximum: the goal of the internal counter
    :type maximum: int or float
    :param steps: interval at which to automatically output current progress
    :type steps: 1
    :param name: name of the counter
    :type name: str
    :param bar_length: length of any progress bar, without the border
    :type bar_length: int
    :param bar_border: characters for borders around any progress bar
    :type bar_border: str
    :param bar_progress: characters for the progress bar
    :type bar_progress: str
    :param bar_remain: characters for the remainder of the progress bar
    :type bar_remain: str
    :param output_format: format string to use for the progress
    :type output_format: str
    :param out_stream: a file-like object to which automatic progress is written
    :type out_stream: :py:class:`file`

    The following format elements are available for ``output_format``:

    - **name** the ``name`` parameter
    - **rate** the rate at which the progress advances
    - **percent** progress in percent, e.g. ``26%``
    - **counter** internal counter state, e.g. ``127/873``
    - **bar** a progress bar, e.g. ``[=> .......]``
    - **percent_bar** combines **bar** and **percent**, e.g. ``[====94%=> ]``
    - **counter_bar** combines **bar** and **counter**, e.g. ``[=> .1/9...]``

    :note: In order to have the progress update the same line progressively, the
           ``output_format`` **must** begin with a carriage return (``\\r``) and
           **not** end with a newline (``\\n``). As there are usecase which might
           desire non-progressive updates, this is not enforced.
    """
    def __init__(self, maximum=100, steps=1, name="Progress", bar_length=20, bar_border="[]", bar_progress="=>", bar_remain=" .", output_format="\r%(name)s: %(percent_bar)s %(rate)s", out_stream=sys.stderr):
        self._count = 0
        self._stime = time.time()
        self.maximum = maximum
        self.steps = steps
        self.name = name
        self.bar_length = bar_length
        self.bar_border = bar_border
        self.bar_progress = bar_progress
        self.bar_remain = bar_remain
        self.output_format = output_format
        self.out_stream = out_stream

    def step(self):
        """
        Advance the progress by 1 and display the status if appropriate
        """
        self._count += 1
        if self._count % self.steps < 1:
            self.emit()

    def add(self, count=1):
        """
        Advance the progress and display the status if appropriate

        :param count: how far to advance the counter
        :type count: int or float
        """
        self._count += count
        if self._count % self.steps <= count:
            self.emit()

    def emit(self):
        """
        Output the current progress to ``out_stream``
        """
        elements = self._make_elements()
        self.out_stream.write(self.output_format%elements)
        self.out_stream.flush()

    def __repr__(self):
        return "%s(count=%s, maximum=%s)"%(self.__class__.__name__, self._count, self.maximum)

    def __str__(self):
        elements = self._make_elements()
        return (self.output_format%elements).replace("\n", "").replace("\r", "")

    def _make_elements(self):
        rate, r_max = self._make_rate()
        percent, p_max = self._make_percent()
        counter, c_max = self._make_counter()
        bar, b_max = self._make_bar()
        percent_bar, pb_max = self._make_count_bar(counter=percent, bar=bar, counter_width=p_max)
        counter_bar, cb_max = self._make_count_bar(counter=counter, bar=bar, counter_width=c_max)
        return {"name":self.name, "counter_bar":counter_bar, "counter":counter, "percent_bar":percent_bar, "bar":bar, "percent":percent, "rate":rate}

    def _make_rate(self):
        rate = self._count / (time.time() - self._stime)
        r_str = numeric_prefix(rate, pow2=False) + "Hz"
        return r_str, len(r_str)

    def _make_percent(self):
        progress = min(100.0, 100.0*self._count / self.maximum)
        return "%d%%" % progress, 3

    def _make_counter(self):
        return "%d/%d" % (self._count, self.maximum), len(str(self.maximum))*2+1

    def _make_bar(self):
        progress = min(1.0, 1.0*self._count / self.maximum)
        bar_progress = int(progress*self.bar_length)
        if bar_progress < 1:
            bar_str = self.bar_remain[-1] * self.bar_length
        elif bar_progress == 1:
            bar_str = self.bar_progress[-1] + self.bar_remain[0] + self.bar_remain[-1] * (self.bar_length-2)
        elif bar_progress == self.bar_length:
            bar_str = self.bar_progress[0] * self.bar_length
        elif bar_progress == self.bar_length - 1:
            bar_str = self.bar_progress[0] * (bar_progress-1) + self.bar_progress[-1] + self.bar_remain[0]
        else:
            bar_str = self.bar_progress[0] * (bar_progress-1) + self.bar_progress[-1] + self.bar_remain[0] + self.bar_remain[-1] * (self.bar_length-bar_progress-1)
        if self.bar_border:
            return self.bar_border[0] + bar_str + self.bar_border[-1], self.bar_length + 2
        return bar_str, self.bar_length

    def _make_count_bar(self, counter, bar, counter_width=None):
        if counter_width is None:
            counter_width = len(counter)
        # right-centered adjust:
        # counter is either equaly close to both sides
        # [> .7%...]
        # [===70%=> ]
        # or one closer to the right
        # [> ..7%...]
        # [===70%=>]
        # Since python integer division ALWAYS rounds down, the following gives
        # us ALWAYS either the equal distance or the smaller distance...
        r_barlength = (len(bar) - counter_width) / 2
        # ...and this gives us always the remaining distance.
        l_barlength=len(bar)-r_barlength-len(counter)
        count_bar = bar[:l_barlength] + counter + bar[-r_barlength:]
        return count_bar, self.bar_length + 2