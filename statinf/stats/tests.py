import numpy as np
import math
from scipy import stats as scp

from . import descriptive as desc
from ..misc import test_summary


# One sample Student test
def ttest(x, mu=0, alpha=0.05, is_bernoulli=False, two_sided=True, return_tuple=False):
    """One sample Student's test.

        In the two-sided setup, we aim at testing:

        .. math:: H_{0}: \\bar{X} = \\mu \\text{  against  } H_{1}: \\bar{X} \\neq \\mu

        The one-sided setup tests :math:`H_{0}: \\bar{X} \\leq \\mu` against :math:`H_{0}: \\bar{X} > \\mu`.

        The p-value is computed as:

        .. math:: \\mathbb{P}(|Z| \\geq |t| \\mid H_{0} \\text{ holds})

        with, under :math:`H_{0}`:

        .. math:: t = \\dfrac{\\bar{X}_{1} - \\mu }{ \\dfrac{s}{\\sqrt{n}} } \\sim \\mathcal{N}(0, 1)

        if :math:`s = \\mathbb{V}(\\mathbf{X})` is known or if :math:`n \\gg 30`, otherwise :math:`t \\sim \\mathcal{T}_{n - 1}`,
        a Student distribution with :math:`n-1` degrees of freedom.
        In case of a bernoulli distribution, then :math:`s = \\mu(1 - \\mu)`.

    :param x: Input variable. Format can be :obj:`numpy.array`, :obj:`list` or :obj:`pandas.Series`.
    :type x: :obj:`numpy.array`
    :param mu: Theoretical mean to be evaluated in the null hypothesis, defaults to 0.
    :type mu: :obj:`int`, optional
    :param alpha: Confidence level, defaults to 0.05.
    :type alpha: :obj:`float`, optional
    :param is_bernoulli: Input value follows a Bernoulli distribution, i.e. :math:`\\mathbf{X} \\sim \\mathcal{B}(p)` with :math:`p \\in [0, 1]`, defaults to False.
    :type is_bernoulli: :obj:`bool`, optional
    :param two_sided: Perform a two-sided test, defaults to True.
    :type two_sided: :obj:`bool`, optional
    :param return_tuple: Return a tuple with t statistic, critical value and p-value, defaults to False.
    :type return_tuple: :obj:`bool`, optional

    :example:

    >>> from statinf import stats
    >>> stats.ttest([30.02, 29.99, 30.11, 29.97, 30.01, 29.99], mu=30)
    ... +------------------------------------------------------------+
    ... |                   One Sample Student test                  |
    ... +------------+----------------+------------+---------+-------+
    ... |     df     | Critical value |    T-value | p-value |   H0  |
    ... +------------+----------------+------------+---------+-------+
    ... |          5 |   2.5705818366 |  0.7392961 | 0.49295 | True  |
    ... +------------+----------------+------------+---------+-------+
    ... * Confidence level is 95.0%, we need p > 0.025 for two-sided test
    ... * We cannot reject the hypothesis H0: X_bar = 30

    :reference: * DeGroot, M. H., & Schervish, M. J. (2012). Probability and statistics. Pearson Education.
        * Student. (1908). The probable error of a mean. Biometrika, 1-25.

    :return: Summary for the test or tuple statistic, critical value, p-value.
    :rtype: :obj:`str` or :obj:`tuple`
    """

    # Define test degrees of freedom
    if two_sided:
        quant_order = 1 - (alpha / 2)
        h0 = f'X_bar = {mu}'
        h1 = f'X_bar != {mu}'
    else:
        quant_order = 1 - alpha
        h0 = f'X_bar <= {mu}'
        h1 = f'X_bar > {mu}'

    # Input vector as array
    x = np.asarray(x)
    # Sample size
    n = len(x)

    # Empirical mean
    x_bar = x.mean()
    # s estimator (variance)
    if is_bernoulli:
        s2 = x_bar * (1 - x_bar)
    else:
        s2 = desc.var(x)

    # Degrees of freedom
    df = n - 1

    # T statistic
    t = (x_bar - mu) / (math.sqrt(s2 / n))
    if two_sided:
        t = math.fabs(t)
    # p and critical values
    p = 2.0 * (1.0 - scp.t.cdf(t, df=df))

    if n > 30:
        cv = scp.norm.ppf(quant_order)
    else:
        cv = scp.t.ppf(quant_order, df=df)

    _summ = test_summary(df=df, critical_value=cv, t_value=t,
                         p_value=p,
                         title='One Sample Student test',
                         h0=h0, h1=h1,
                         alpha=alpha)

    if return_tuple:
        return t, cv, p
    else:
        return _summ


# 2 samples Student test
def ttest_2samp(x1, x2, alpha=0.05, paired=False, is_bernoulli=False, two_sided=True, return_tuple=False):
    """Two samples Student's test.

        If the samples are independent (:math:`X_{1} \\bot X_{2}`), we test:

        .. math:: H_{0}: \\bar{X}_{1} = \\bar{X}_{2} \\text{  against  } H_{1}: \\bar{X}_{1} \\neq \\bar{X}_{2}

        The test statistic is:

        .. math:: t = \\dfrac{\\bar{X}_{1} - \\bar{X}_{2} }{ \\sqrt{ \\dfrac{(n_{1} - 1) s^{2}_{1} + (n_{2} - 1) s^{2}_{2}}{n_{1} + n_{2} - 1} } \\sqrt{\\dfrac{1}{n_{1}} + \\dfrac{1}{n_{2}}} }

        where:

            * :math:`t \\sim \\mathcal{T}_{n_{1} + n_{2} - 2}`, if :math:`\\mathbf{X} \\sim \\mathcal{N}(\\mu_{X}, \\sigma^{2}_{X})` and :math:`\\mathbf{Y} \\sim \\mathcal{N}(\\mu_{Y}, \\sigma^{2}_{Y})`
            * :math:`t \\sim \\mathcal{N}(0, 1)`, if :math:`n_{1} \\gg 30` and :math:`n_{2} \\gg 30`

        If samples are paired:

        .. math:: H_{0}: \\bar{X}_{1} = \\bar{X}_{2} \\Leftrightarrow \\bar{X}_{1} - \\bar{X}_{2} = 0 \\Leftrightarrow \\bar{X}_{D} = 0

        We then compared a one sample test where the tested vector is the difference between both vectors :math:`X_{D} = X_{1} - X_{2}`
        for which we compare whether it is equal to 0.

    :param x1: Input variable. Format can be :obj:`numpy.array`, :obj:`list` or :obj:`pandas.Series`.
    :type x1: :obj:`numpy.array`
    :param x2: Input variable. Format can be :obj:`numpy.array`, :obj:`list` or :obj:`pandas.Series`.
    :type x2: :obj:`numpy.array`
    :param alpha: Confidence level, defaults to 0.05.
    :type alpha: :obj:`float`, optional
    :param paired: Performs one sample test of the difference if samples are paired, defaults to False.
    :type paired: :obj:`bool`, optional
    :param is_bernoulli: Input variables follow a Bernoulli distribution, i.e. :math:`\\mathbf{X} \\sim \\mathcal{B}(p)` with :math:`p \\in [0, 1]`, defaults to False.
    :type is_bernoulli: :obj:`bool`, optional
    :param two_sided: Perform a two-sided test, defaults to True.
    :type two_sided: :obj:`bool`, optional
    :param return_tuple: Return a tuple with t statistic, critical value and p-value, defaults to False.
    :type return_tuple: :obj:`bool`, optional

    :example:

    >>> from statinf import stats
    >>> a = [30.02, 29.99, 30.11, 29.97, 30.01, 29.99]
    >>> b = [29.89, 29.93, 29.72, 29.98, 30.02, 29.98]
    >>> stats.ttest_2samp(a, b)
    ... +------------------------------------------------------------+
    ... |                   Two Samples Student test                 |
    ... +------------+----------------+------------+---------+-------+
    ... |     df     | Critical value |    T-value | p-value |   H0  |
    ... +------------+----------------+------------+---------+-------+
    ... |         10 |  -1.8124611228 |  1.1310325 | 0.28444 | True  |
    ... +------------+----------------+------------+---------+-------+
    ...  * Confidence level is 95.0%, we need p > 0.05
    ...  * We cannot reject the hypothesis H0: X1 = X2
    ...  * Samples with unequal variances
    ...  * Same sample sizes

    :reference: * DeGroot, M. H., & Schervish, M. J. (2012). Probability and statistics. Pearson Education.
        * Student. (1908). The probable error of a mean. Biometrika, 1-25.

    :return: Summary for the test or tuple statistic, critical value, p-value.
    :rtype: :obj:`str` or :obj:`tuple`
    """
    x = np.asarray(x1)
    y = np.asarray(x2)

    # Define test degrees of freedom
    if two_sided:
        quant_order = 1 - (alpha / 2)
        h0 = 'X1_bar = X2_bar'
        h1 = 'X1_bar != X2_bar'
    else:
        quant_order = 1 - alpha
        h0 = 'X1 <= X2'
        h1 = 'X1 > X2'

    # Sample sizes
    n1, n2 = len(x), len(y)

    if paired:
        # If samples are paired, we perform a 1-sample student test
        # We compare if the difference is different from 0.
        mean1, mean2 = x.mean(), y.mean()
        d = x - y
        t, cv, p = ttest(d, alpha=alpha, return_tuple=True)
        df = len(d)
    else:
        # Else samples are independent
        # Compute means
        mean1, mean2 = x.mean(), y.mean()
        # Compute standard deviations
        if is_bernoulli:
            s1 = mean1 * (1 - mean1)
            s2 = mean2 * (1 - mean2)
        else:
            s1 = desc.var(x)
            s2 = desc.var(y)
        # Compute grouped variance
        sd = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
        # Degrees of freedom
        df = n1 + n2 - 2
        # Calculate the t statistic
        t = (mean1 - mean2) / sd

        # calculate the critical value
        cv = scp.t.ppf(quant_order, df)
        # calculate the p-value
        if (n1 > 30) & (n2 > 30):
            p = 2.0 * (1.0 - scp.norm.cdf(math.fabs(t)))
        else:
            p = 2.0 * (1.0 - scp.t.cdf(math.fabs(t), df=df))

    extra = f" * E(X1) = {round(mean1, 3)} and E(X2) = {round(mean2, 3)} \n"
    extra += " * Performed test for paired samples \n" if paired else ''
    extra += " * Large sample sizes, t ~ N(0, 1) from CLT" if (n1 > 30) & (n2 > 30) else ' * Small sample sizes, assumed t ~ T(n-1)'

    _summ = test_summary(df=df, critical_value=cv, t_value=t,
                         p_value=p,
                         title='Two Samples Student test',
                         h0=h0, h1=h1,
                         alpha=alpha,
                         extra=extra)

    if return_tuple:
        return t, cv, p
    else:
        return _summ


# Kolmogorov-Smirnov test
def kstest(x1, x2='normal', alpha=0.05, return_tuple=False, **kwargs):
    """Kolmogorov-Smirnov test for sample tests.

        We test if two samples come from the same distribution :math:`H_{0}: F(x) = G(x)` against :math:`H_{1}: F(x)` follows a distribution that :math:`G(x)`.

        The statistic is:

        .. math:: D_{mn} = \\sup_{-\\infty < x < + \\infty} |F_{n}(x) - G_{m}(x)|

        and the critical value is given by:

        .. math:: c = \\mathbb{P} \\left[ \\left( \\dfrac{mn}{n + m} \\right)^{2} D_{mn} < K_{\\alpha} \\right]

        where :math:`K_{\\alpha}` represents the quantile of order :math:`\\alpha` from a Kolmogorov distribution.

        This test is an alternative to the :math:`\\chi^{2}`-test where we compare two distributions.
        By comparing an unknown empirical distribution :math:`F_{n}` with a distribution :math:`G_{n}` pulled from a known function, we can assess whether :math:`F_{n}` follows the same distribution as :math:`G_{n}`.
        For instance, when comparing :math:`F_{n}` (unknown) to :math:`G_{n} \\sim \\mathcal{N}(\\mu, \\sigma^{2})`,
        not rejecting :math:`H_{0}` would mean that we cannot reject the hypothesis that :math:`F_{n} \\sim \\mathcal{N}(\\mu, \\sigma^{2})`.

    :param x1: Input variable. Format can be :obj:`numpy.array`, :obj:`list` or :obj:`pandas.Series`.
    :type x1: :obj:`numpy.array`
    :param x2: Sample to be compared. Can be external empirical sample in the same format as :obj:`x1` or the name of a cdf which can be 'normal', 'beta', 'gamma', 'poisson', 'chisquare', 'exponential', 'gamma', defaults to 'normal'.
    :type x2: :obj:`str`, optional
    :param alpha: Confidence level, defaults to 0.05.
    :type alpha: :obj:`float`, optional
    :param return_tuple: Return a tuple with K statistic, critical value and p-value, defaults to False.
    :type return_tuple: :obj:`bool`, optional

    :example:

    >>> from statinf import stats
    >>> import numpy as np
    >>> stats.kstest(np.random.normal(size=100))
    ... +------------------------------------------------------------+
    ... |                   Kolmogorov-Smirnov test                  |
    ... +------------+----------------+------------+---------+-------+
    ... | D value    | Critical value | K-value    | p-value |   H0  |
    ... +------------+----------------+------------+---------+-------+
    ... |       0.09 |  1.35809863932 |  0.6363961 | 0.81275 | True  |
    ... +------------+----------------+------------+---------+-------+
    ...  * We cannot reject the hypothesis H0: F(x) ~ normal
    ...  * Confidence level is 95.0%, we need p > 0.05

    :reference: * DeGroot, M. H., & Schervish, M. J. (2012). Probability and statistics. Pearson Education.
        * Kolmogorov-Smirnov, A. N., Kolmogorov, A., & Kolmogorov, M. (1933). Sulla determinazione empírica di uma legge di distribuzione.
        * Marsaglia, G., Tsang, W. W., & Wang, J. (2003). `Evaluating Kolmogorov’s distribution <https://www.jstatsoft.org/article/view/v008i18>`_. Journal of Statistical Software, 8(18), 1-4.

    :return: Summary for the test or tuple statistic, critical value, p-value.
    :rtype: :obj:`str` or :obj:`tuple`
    """

    quant_order = 1 - alpha
    # Format x1
    x = np.asarray(x1)
    n = len(x)

    if type(x2) == str:
        h0 = f"F(x) ~ {x2}"
        h1 = f"F(x) is not {x2}"
        if x2.lower() in ['normal', 'norm', 'gaussian', 'gauss']:
            y = np.random.normal(size=n, **kwargs)
        elif x2.lower() in ['beta']:
            y = np.random.beta(size=n, **kwargs)
        elif x2.lower() in ['gamma']:
            y = np.random.gamma(size=n, **kwargs)
        elif x2.lower() in ['poisson']:
            y = np.random.poisson(size=n, **kwargs)
        elif x2.lower() in ['chisquare', 'chi-square', 'chi2', 'x2']:
            y = np.random.chisquare(size=n, **kwargs)
        elif x2.lower() in ['exponential', 'expo']:
            y = np.random.exponential(size=n, **kwargs)
        elif x2.lower() in ['gumbel']:
            y = np.random.gumbel(size=n, **kwargs)
        else:
            raise ValueError('cdf value for x2 is not valid.')
    else:
        y = np.asarray(x2)
        h0 = "F(x) = G(x)"
        h1 = "F(x) and G(x) have different distributions"

    # Sample sizes
    m = len(y)
    # Sort values and concatenate to one array
    x_sort = np.sort(x)
    y_sort = np.sort(y)
    concat_data = np.concatenate([x_sort, y_sort])
    # Build sort distributions to compute the max deviance
    cdf1 = np.searchsorted(x_sort, concat_data, side='right') / float(n)
    cdf2 = (np.searchsorted(y_sort, concat_data, side='right')) / float(m)
    # Find the max deviance
    d = np.max(np.absolute(cdf1 - cdf2))
    # Compute K value
    k = d * math.sqrt((n * m) / (n + m))
    cv = scp.kstwobign.ppf(quant_order)
    p = 1.0 - scp.kstwobign.cdf(math.fabs(k))

    _summ = test_summary(df=n, critical_value=cv, t_value=k,
                         p_value=p, alpha=alpha,
                         title='Kolmogorov-Smirnov test',
                         h0=h0, h1=h1,
                         extra=f' * The D-value is: {round(d, 5)}')

    if return_tuple:
        return k, cv, p
    else:
        return _summ
