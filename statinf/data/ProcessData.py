import numpy as np
import pandas as pd
import re
import warnings
from types import SimpleNamespace


# Ranking data

def rankdata(x):
    """Assigns rank to data.
    This is mainly used for analysis like Spearman's correlation.

    :param x: Input vector. Format can be :obj:`numpy.array`, :obj:`list` or :obj:`pandas.Series`.
    :type x: :obj:`numpy.array`

    :example:

    >>> rankdata([2., 5.44, 3.93, 3.3, 1.1])
    ... array([1, 4, 3, 2, 0])

    :return: Vector with ranked values.
    :rtype: :obj:`numpy.array`
    """
    x_arr = np.asarray(x)
    sorted_array = sorted(x_arr)
    rk = [sorted_array.index(i) for i in x_arr]
    return np.array(rk)


#######################################################################################################################

# Parse formula and data transformations

def parse_formula(formula, data, check_values=True, return_all=False):
    """This function is used in regression models in order to apply transformations on the data from a formula.
    It allows to apply transformations from a :obj:`str` formula. See below for examples.

    :param formula: Regression formula to be run of the form :obj:`y ~ x1 + x2`. Accepted functions are:

        * :math:`\\log(x)` \\: :obj:`log(X)`
        * :math:`\\exp(x)` \\: :obj:`exp(X)`
        * :math:`\\sqrt{x}` \\: :obj:`sqrt(X)`
        * :math:`\\cos(x)` \\: :obj:`cos(X)`
        * :math:`\\sin(x)` \\: :obj:`sin(X)`
        * :math:`x^{z}` \\: :obj:`X ** Z`
        * :math:`\\dfrac{x}{z}` \\: :obj:`X/Z`
        * :math:`x \\times z` \\: :obj:`X*Z`

    :type formula: :obj:`str`
    :param data: Data on which to perform the transformations.
    :type data: :obj:`pandas.DataFrame`
    :param check_values: For each transformation check whether the data range satisfy the domain definition of the function, defaults to True.
    :type check_values: bool, optional
    :param return_all: Returns the transformed data, column :obj:`Y` and columns :obj:`X`, defaults to False.
    :type return_all: bool, optional

    :example:

    >>> from statinf.data import parse_formula
    >>> print(input_df)
    ... +-----------+-----------+-----------+
    ... |        X1 |        X2 |         Y |
    ... +-----------+-----------+-----------+
    ... |  0.555096 |  0.681083 | -1.383428 |
    ... |  1.155661 |  0.391129 | -7.780989 |
    ... | -0.299251 | -0.445602 | -8.146673 |
    ... | -0.978311 |  1.312146 |  8.653818 |
    ... | -0.225917 |  0.522016 | -9.684332 |
    ... +-----------+-----------+-----------+
    >>> form = 'Y ~ X1 + X2 + exp(X2) + X1*X2'
    >>> new_df = parse_formula(form, data=input_df)
    >>> print(new_df)
    ... +-----------+-----------+-----------+-----------+-----------+
    ... |        X1 |        X2 |         Y |   exp(X2) |     X1*X2 |
    ... +-----------+-----------+-----------+-----------+-----------+
    ... |  0.555096 |  0.681083 | -1.383428 |  1.976017 |  0.378066 |
    ... |  1.155661 |  0.391129 | -7.780989 |  1.478649 |  0.452012 |
    ... | -0.299251 | -0.445602 | -8.146673 |  0.640438 |  0.133347 |
    ... | -0.978311 |  1.312146 |  8.653818 |  3.714134 | -1.283687 |
    ... | -0.225917 |  0.522016 | -9.684332 |  1.685422 | -0.117932 |
    ... +-----------+-----------+-----------+-----------+-----------+

    :raises ValueError: Returns an error when the data cannot satisfy the domain definition for the required transformation.

    :return: Transformed data set
    :rtype: :obj:`pandas.DataFrame`
    """
    warnings.filterwarnings('ignore')
    # Parse formula
    no_space_formula = formula.replace(' ', '')
    Y_col = no_space_formula.split('~')[0]
    X_col = no_space_formula.split('~')[1].split('+')

    # Non-linear transformations
    log_cols = [re.search('(?<=log\\().*?(?=\\))', x).group(0) for x in X_col if re.findall('log\\(', x)]  # log
    exp_cols = [re.search('(?<=exp\\().*?(?=\\))', x).group(0) for x in X_col if re.findall('exp\\(', x)]  # exp
    sqrt_cols = [re.search('(?<=sqrt\\().*?(?=\\))', x).group(0) for x in X_col if re.findall('sqrt\\(', x)]  # sqrt
    cos_cols = [re.search('(?<=cos\\().*?(?=\\))', x).group(0) for x in X_col if re.findall('cos\\(', x)]  # cos
    sin_cols = [re.search('(?<=sin\\().*?(?=\\))', x).group(0) for x in X_col if re.findall('sin\\(', x)]  # sin

    # Transformation functions
    transformations_functional = {'log': {'func': np.log, 'cols': log_cols},
                                  'exp': {'func': np.exp, 'cols': exp_cols},
                                  'cos': {'func': np.cos, 'cols': cos_cols},
                                  'sin': {'func': np.sin, 'cols': sin_cols},
                                  'sqrt': {'func': np.sqrt, 'cols': sqrt_cols},
                                  }
    # Apply transformations
    for key, transformation in transformations_functional.items():
        for c in transformation['cols']:
            col_to_transform = c  # .split('(')[1].split(')')[0]
            # Transform
            data.loc[:, f'{key}({col_to_transform})'] = transformation['func'](data[col_to_transform])

    # Multiplications, power and ration functions
    pow_cols = [x for x in X_col if re.findall('[a-zA-Z0-9\\(\\)][*][*][a-zA-Z0-9]', x)]  # X1 ** x
    inter_cols = [x for x in X_col if re.findall('[a-zA-Z0-9\\(\\)][*][a-zA-Z0-9]', x)]  # X1 * X2
    div_cols = [x for x in X_col if re.findall('[a-zA-Z0-9\\(\\)][/][a-zA-Z0-9]', x)]  # X1 / X2

    # Exponents
    for c in pow_cols:
        c_left = c.split('**')[0]
        c_power = c.split('**')[1]
        # Get components as number or column from data
        left = data[c_left].values if c_left in data.columns else float(c_left)
        power = data[c_power].values if c_power in data.columns else float(c_power)
        # Transform
        data.loc[:, c] = left ** power
    # Multiplications
    for c in inter_cols:
        c_left = c.split('*')[0]
        c_right = c.split('*')[1]
        # Get components as number or column from data
        try:
            left = data[c_left].values if c_left in list(data.columns) + X_col else float(c_left)
            right = data[c_right].values if c_right in list(data.columns) + X_col else float(c_right)
        except Exception:
            raise ValueError(f'Columns {c_left} or {c_right} not found in data.')
        # Transform
        data.loc[:, c] = left * right
    # Divide
    for c in div_cols:
        c_num = c.split('/')[0]
        c_denom = c.split('/')[1]
        # Get components as number or column from data
        num = data[c_num].values if c_num in list(data.columns) + X_col else float(c_num)
        denom = data[c_denom].values if c_denom in list(data.columns) + X_col else float(c_denom)
        if check_values:
            assert (denom == 0.).sum() == 0, f'Column {col_to_transform} contains null values.'
        # Transform
        data.loc[:, c] = num / denom
    if '1' in X_col:
        data['1'] = 1

    # Putting pandas' warning message back
    warnings.filterwarnings('default')

    if return_all:
        return data, X_col, Y_col
    else:
        return data


#######################################################################################################################

# Adding One Hot Encoding
def OneHotEncoding(data, columns, drop=True, verbose=False):
    """Performs One Hot Encoding (OHE) usally used in Machine Learning.

    :param data: Data Frame on which we apply One Hot Encoding.
    :type data: :obj:`pandas.DataFrame`
    :param columns: Column to be converted to dummy variables.
    :type columns: :obj:`list`
    :param drop: Drop the column that needs to be converted to dummies, defaults to True.
    :type drop: :obj:`bool`, optional
    :param verbose: Display progression, defaults to False.
    :type verbose: :obj:`bool`, optional

    :example:

        >>> from statinf.data import OneHotEncoding
        >>> print(df)
        ... +----+--------+----------+-----+
        ... | Id | Gender | Category | Age |
        ... +----+--------+----------+-----+
        ... |  1 | Male   |        A |  23 |
        ... |  2 | Female |        B |  21 |
        ... |  3 | Female |        A |  31 |
        ... |  4 | Male   |        C |  22 |
        ... |  5 | Female |        A |  26 |
        ... +----+--------+----------+-----+
        >>> # Encoding columns "Gender" and "Category"
        >>> new_df = OneHotEncoding(df, columns=["Gender", "Category"])
        >>> print(new_df)
        ... +----+---------------+------------+------------+-----+
        ... | Id | Gender_Female | Category_A | Category_B | Age |
        ... +----+---------------+------------+------------+-----+
        ... |  1 |             0 |          1 |          0 |  23 |
        ... |  2 |             1 |          0 |          1 |  21 |
        ... |  3 |             1 |          1 |          0 |  31 |
        ... |  4 |             0 |          0 |          0 |  22 |
        ... |  5 |             1 |          1 |          0 |  26 |
        ... +----+---------------+------------+------------+-----+

    :return: Transformed data with One Hot Encoded variables.
    :rtype: :obj:`pandas.DataFrame`
    """

    dataset = data.copy()

    try:
        if dataset.meta._ohe_exists:
            dataset.meta._ohe_exists = True
    except Exception:
        dataset.meta = SimpleNamespace()
        dataset.meta._ohe_exists = True
        dataset.meta._ohe = {}

    cols = [columns] if type(columns) == str else columns

    # Start encoding column by column
    for column in cols:
        # Get all values from the column
        all_values = dataset[column].unique()
        # Add column metadata
        dataset.meta._ohe.update({column: [f'{column}_{val}' for val in all_values]})

        # Encode values
        for val in all_values:
            if verbose:
                print('Encoding for value: ' + str(val))
            colname = column + '_' + str(val)
            dataset.loc[:, colname] = 0
            dataset.loc[dataset[column] == val, colname] = 1

        if drop:
            dataset.drop(columns=[column], inplace=True)
    
    return(dataset)


#######################################################################################################################

# convert an array of values into a dataset matrix: used for LSTM data pre-processing
def create_dataset(data, look_back=1):
    """Function to convert a DataFrame to array format readable for keras LSTM.

    :param data: DataFrame on which to aply the transformation.
    :type data: :obj:`pandas.DataFrame`
    :param look_back: Number of periods in the past to consider (defaults 1)., defaults to 1
    :type look_back: :obj:`int`, optional

    :example:
        >>> from statinf.data import create_dataset
        >>> create_dataset(df)

    :return: * Features X converted for keras LSTM.
        * Dependent variable Y converted for keras LSTM.
    :rtype: * :obj:`numpy.array`
        * :obj:`numpy.array`
    """

    dataset = data.copy()

    dataX, dataY = [], []
    for i in range(len(dataset) - look_back - 1):
        a = dataset[i:(i + look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + look_back, 0])
    return np.array(dataX), np.array(dataY)


#######################################################################################################################

# Scale dataset
class Scaler:
    def __init__(self, data, columns):
        """Data scaler.

        :param data: Data set to scale.
        :type data: :obj:`pandas.DataFrame`
        :param columns: Columns to scale.
        :type columns: :obj:`list`

        :example:

            >>> from statinf.data import Scaler, generate_dataset
            >>> coeffs = [1.2556, -0.465, 1.665414, 2.5444, -7.56445]
            >>> data = generate_dataset(coeffs, n=10, std_dev=2.6)
            >>> # Original dataset
            >>> print(data)
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |        X0 |        X1 |        X2 |        X3 |        X4 |         Y |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |  0.977594 |  1.669510 | -1.385569 |  0.696975 | -1.207098 |  8.501692 |
            ... | -0.953802 |  1.025392 | -0.639291 |  0.658251 |  0.746814 | -7.186085 |
            ... | -0.148140 | -0.972473 |  0.843746 |  1.306845 |  0.269834 |  1.939924 |
            ... |  0.499385 | -1.081926 |  2.646441 |  0.910503 |  0.857189 |  0.389257 |
            ... | -0.563977 | -0.511933 | -0.726744 | -0.630345 | -0.486822 | -0.125787 |
            ... | -0.434994 | -0.396210 |  1.101739 | -0.660236 | -1.197566 |  7.735832 |
            ... |  0.032478 | -0.114952 | -0.097337 |  1.794769 |  1.239423 | -5.510332 |
            ... |  0.085569 | -0.600019 |  0.224186 |  0.301771 |  1.278387 | -8.648084 |
            ... | -0.028844 | -0.329940 | -0.301762 |  0.946077 | -0.359133 |  5.099971 |
            ... | -0.665312 |  0.270254 | -1.263288 |  0.545625 |  0.499162 | -6.126528 |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            >>> # Load scaler class
            >>> scaler = Scaler(data=data, columns=['X1', 'X2'])
            >>> # Scale our dataset with MinMax method
            >>> scaled_df = scaler.MinMax()
            >>> print(scaled_df)
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |        X0 |        X1 |        X2 |        X3 |        X4 |         Y |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |  0.977594 |  1.000000 |  0.000000 |  0.696975 | -1.207098 |  8.501692 |
            ... | -0.953802 |  0.765898 |  0.185088 |  0.658251 |  0.746814 | -7.186085 |
            ... | -0.148140 |  0.039781 |  0.552904 |  1.306845 |  0.269834 |  1.939924 |
            ... |  0.499385 |  0.000000 |  1.000000 |  0.910503 |  0.857189 |  0.389257 |
            ... | -0.563977 |  0.207162 |  0.163399 | -0.630345 | -0.486822 | -0.125787 |
            ... | -0.434994 |  0.249221 |  0.616890 | -0.660236 | -1.197566 |  7.735832 |
            ... |  0.032478 |  0.351444 |  0.319501 |  1.794769 |  1.239423 | -5.510332 |
            ... |  0.085569 |  0.175148 |  0.399244 |  0.301771 |  1.278387 | -8.648084 |
            ... | -0.028844 |  0.273307 |  0.268801 |  0.946077 | -0.359133 |  5.099971 |
            ... | -0.665312 |  0.491445 |  0.030328 |  0.545625 |  0.499162 | -6.126528 |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            >>> # Unscale the new dataset to retreive previous data scale
            >>> unscaled_df = scaler.unscaleMinMax(scaled_df)
            >>> print(unscaled_df)
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |        X0 |        X1 |        X2 |        X3 |        X4 |         Y |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
            ... |  0.977594 |  1.669510 | -1.385569 |  0.696975 | -1.207098 |  8.501692 |
            ... | -0.953802 |  1.025392 | -0.639291 |  0.658251 |  0.746814 | -7.186085 |
            ... | -0.148140 | -0.972473 |  0.843746 |  1.306845 |  0.269834 |  1.939924 |
            ... |  0.499385 | -1.081926 |  2.646441 |  0.910503 |  0.857189 |  0.389257 |
            ... | -0.563977 | -0.511933 | -0.726744 | -0.630345 | -0.486822 | -0.125787 |
            ... | -0.434994 | -0.396210 |  1.101739 | -0.660236 | -1.197566 |  7.735832 |
            ... |  0.032478 | -0.114952 | -0.097337 |  1.794769 |  1.239423 | -5.510332 |
            ... |  0.085569 | -0.600019 |  0.224186 |  0.301771 |  1.278387 | -8.648084 |
            ... | -0.028844 | -0.329940 | -0.301762 |  0.946077 | -0.359133 |  5.099971 |
            ... | -0.665312 |  0.270254 | -1.263288 |  0.545625 |  0.499162 | -6.126528 |
            ... +-----------+-----------+-----------+-----------+-----------+-----------+
        """
        super(Scaler, self).__init__()
        self.data = data.copy()
        self.scalers = {}
        self.columns = list(columns)

        for c in columns:
            _min = self.data[c].min()
            _max = self.data[c].max()
            _mean = self.data[c].mean()
            _std = self.data[c].std()
            _scale_temp = {'min': float(_min),
                           'max': float(_max),
                           'mean': float(_mean),
                           'std': float(_std),
                           }
            self.scalers.update({c: _scale_temp})

    def _col_to_list(self, columns):
        """Transforms column names to be scaled as list.

        :param columns: Column names to be scaled.
        :type columns: :obj:`list` or :obj:`str`

        :return: Column name(s) as a list
        :rtype: :obj:`list`
        """
        if columns is None:
            cols = self.columns
        elif type(columns) == str:
            cols = [columns]
        else:
            cols = columns
        return cols

    def MinMax(self, data=None, columns=None, col_suffix=''):
        """Min-max scaler. Data we range between 0 and 1.

        :param data: Data set to scale, defaults to None, takes data provided in :py:meth:`__init__`.
        :type data: :obj:`pandas.DataFrame`, optional
        :param columns: Columns to be scaled, defaults to None, takes the list provided in :py:meth:`__init__`.
        :type columns: :obj:`list`, optional
        :param col_suffix: Suffix to add to colum names, defaults to '', overrides the existing columns.
        :type col_suffix: :obj:`str`, optional

        :formula: .. math:: x_{\\text{scaled}} = \\dfrac{x - \\min(x)}{\\max(x) - \\min(x)}

        :return: Data set with scaled features.
        :rtype: :obj:`pandas.DataFrame`
        """
        self._minmax_suffix = col_suffix
        cols = self._col_to_list(columns)
        df = self.data if data is None else data.copy()

        for c in cols:
            # Retreive min and max
            _min = self.scalers[c]['min']
            _max = self.scalers[c]['max']
            df[c + col_suffix] = (df[c] - _min) / (_max - _min)
        return df

    def unscaleMinMax(self, data=None, columns=None):
        """Unscale from min-max.
        Retreives data from the same range as the original features.

        :param data: Data set to unscale, defaults to None, takes data provided in :py:meth:`__init__`.
        :type data: :obj:`pandas.DataFrame`, optional
        :param columns: Columns to be unscaled, defaults to None, takes the list provided in :py:meth:`__init__`.
        :type columns: :obj:`list`, optional

        :formula: .. math:: x_{\\text{unscaled}} = x_{\\text{scaled}} \\cdot \\left(\\max(x) - \\min(x) \\right) + \\min(x)

        :return: Unscaled data set.
        :rtype: :obj:`pandas.DataFrame`
        """
        cols = self._col_to_list(columns)
        df = self.data if data is None else data.copy()
        unscale_suffix = '_unscaled' if self._minmax_suffix != '' else ''

        for c in cols:
            # Retreive min and max
            _min = self.scalers[c]['min']
            _max = self.scalers[c]['max']
            df[c + unscale_suffix] = (df[c + self._minmax_suffix] * (_max - _min)) + _min
        return df

    def Normalize(self, center=True, reduce=True, data=None, columns=None, col_suffix=''):
        """Data normalizer.
        Centers and reduces features (from mean and standard deviation).

        :param center: Center the variable, i.e. substract the mean, defaults to True.
        :type center: :obj:`bool`, optional
        :param reduce: Reduce the variable, i.e. devide by standard deviation, defaults to True.
        :type reduce: :obj:`bool`, optional
        :param data: Data set to normalize, defaults to None, takes data provided in :py:meth:`__init__`.
        :type data: :obj:`pandas.DataFrame`, optional
        :param columns: Columns to be normalize, defaults to None, takes the list provided in :py:meth:`__init__`.
        :type columns: :obj:`list`, optional
        :param col_suffix: [description], defaults to ''
        :type col_suffix: :obj:`str`, optional

        :formula: .. math:: x_{\\text{scaled}} = \\dfrac{x - \\bar{x}}{\\sqrt{\\mathbb{V}(x)}}

        :return: Data set with normalized features.
        :rtype: :obj:`pandas.DataFrame`
        """
        self._standard_suffix = col_suffix
        cols = self._col_to_list(columns)
        df = self.data if data is None else data.copy()

        for c in cols:
            # Retreive mean
            if center:
                _mean = self.scalers[c]['mean']
                self.scalers[c].update({'center': True})
            else:
                _mean = 0.
                self.scalers[c].update({'center': False})
            # Retreive std
            if reduce:
                _std = self.scalers[c]['std']
                self.scalers[c].update({'reduce': True})
            else:
                _std = 1.
                self.scalers[c].update({'reduce': False})

            df[c + col_suffix] = (df[c] - _mean) / _std
        return df

    def unscaleNormalize(self, data=None, columns=None):
        """Denormalize data to retreive the same range as the original data set.

        :param data: Data set to unscale, defaults to None, takes data provided in :py:meth:`__init__`.
        :type data: :obj:`pandas.DataFrame`, optional
        :param columns: Columns to be unscaled, defaults to None, takes the list provided in :py:meth:`__init__`.
        :type columns: :obj:`list`, optional

        :formula: .. math:: x_{\\text{unscaled}} = x_{\\text{scaled}} \\cdot \\sqrt{\\mathbb{V}(x)} + \\bar{x}

        :return: De-normalized data set.
        :rtype: :obj:`pandas.DataFrame`
        """
        cols = self._col_to_list(columns)
        df = self.data if data is None else data.copy()
        unscale_suffix = '_unscaled' if self._standard_suffix != '' else ''

        for c in cols:
            # Retreive min and max
            _mean = self.scalers[c]['mean'] if self.scalers[c]['center'] else 0.
            _std = self.scalers[c]['std'] if self.scalers[c]['reduce'] else 1.

            df[c + unscale_suffix] = (df[c + self._standard_suffix] * _std) + _mean

        return df
