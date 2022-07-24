#!/usr/bin/env python

import numpy as np



def flip_source_tasks(source_tasks):
    ''' flip the sign of the source tasks if the
    optimization goal is maximization
    '''
    flipped_source_tasks = []
    for task in source_tasks:
        flipped_source_tasks.append(
            {
                'params': task['params'],
                'values': -1*task['values'],
            }
        )

    return flipped_source_tasks


class Scaler:

    SUPP_TYPES = ['standardization', 'normalization', 'identity']

    ''' scaler for source data
    Args:
        type (str): scaling type, supported are standardization or
                    normalization
        data (str): data type, either params or values
    '''
    def __init__(self, param_type, value_type):
        if not param_type in self.SUPP_TYPES:
            raise NotImplementedError
        else:
            self.param_type = param_type

        if not value_type in self.SUPP_TYPES:
            raise NotImplementedError
        else:
            self.value_type = value_type

        self.is_fit = False


    def _compute_stats(self, source_tasks):
        ''' computes the stats for an entire set of source tasks
        '''
        # join source tasks params
        all_source_params = []
        all_source_values = []
        for task in source_tasks:
            all_source_params.append(task['params'])
            all_source_values.append(task['values'])
        all_source_params = np.concatenate(np.array(all_source_params), axis=0)
        all_source_values = np.concatenate(np.array(all_source_values), axis=0)

        # make sure these are 2d
        assert len(all_source_params.shape)==2
        assert len(all_source_values.shape)==2

        # compute stats for parameters
        param_stats = {}
        if self.param_type == 'normalization':
            param_stats['max'] = np.amax(all_source_params, axis=0)
            param_stats['min'] = np.amin(all_source_params, axis=0)
        elif self.param_type == 'standardization':
            # need the mean and the standard deviation
            param_stats['mean'] = np.mean(all_source_params, axis=0)
            std = np.std(all_source_params, axis=0)
            param_stats['std'] = np.where(std == 0., 1., std)
        self.param_stats = param_stats

        # compute stats for values
        value_stats = {}
        if self.value_type == 'normalization':
            value_stats['max'] = np.amax(all_source_values, axis=0)
            value_stats['min'] = np.amin(all_source_values, axis=0)
        elif self.value_type == 'standardization':
            # need the mean and the standard deviation
            value_stats['mean'] = np.mean(all_source_values, axis=0)
            std = np.std(all_source_values, axis=0)
            value_stats['std'] = np.where(std == 0., 1., std)
        self.value_stats = value_stats


    def fit_transform_tasks(self, source_tasks):
        ''' compute stats for a set of source tasks
        '''
        # register the stats
        self._compute_stats(source_tasks)

        transformed_source_tasks = []

        for task in source_tasks:
            trans_task = {}
            # params
            if self.param_type == 'normalization':
                trans_task['params'] = self.normalize(
                    task['params'], self.param_stats['min'], self.param_stats['max'], 'forward'
                )
            elif self.param_type == 'standardization':
                trans_task['params'] = self.standardize(
                    task['params'], self.param_stats['mean'], self.param_stats['std'], 'forward'
                )
            elif self.param_type == 'identity':
                trans_task['params'] = self.identity(task['params'], 'forward')
            # values
            if self.value_type == 'normalization':
                trans_task['values'] = self.normalize(
                    task['values'], self.value_stats['min'], self.value_stats['max'], 'forward'
                )
            elif self.value_type == 'standardization':
                trans_task['values'] = self.standardize(
                    task['values'], self.value_stats['mean'], self.value_stats['std'], 'forward'
                )
            elif self.value_type == 'identity':
                trans_task['values'] = self.identity(task['values'], 'forward')

            transformed_source_tasks.append(trans_task)

        return transformed_source_tasks

    def identity(self, x, direction):
        ''' identity transformation
        '''
        return x

    def standardize(self, x, mean, std, direction):
        ''' standardize the data given parameters
        '''
        if direction == 'forward':
            return (x - mean) / std
        elif direction == 'reverse':
            return x*std + mean


    def normalize(self, x, min, max, direction):
        ''' normalize the data given parameters
        '''
        if direction == 'forward':
            return (x - min) / (max - min)
        elif direction == 'reverse':
            return x*(max - min) + min


    def transform_tasks(self, tasks):
        ''' transform a set of tasks
        '''
        transformed_source_tasks = []
        for task in tasks:
            trans_task = {}
            # params
            trans_task['params'] = self.transform(task['params'], type='params')
            # values
            trans_task['values'] = self.transform(task['values'], type='values')
        transformed_source_tasks.append(trans_task)

        return transformed_source_tasks


    def transform(self, sample, type):
        ''' transforms a sample
        '''
        # make sure this sample is 2d array
        assert len(sample.shape)==2

        if type == 'params':
            if self.param_type == 'normalization':
                return self.normalize(sample, self.param_stats['min'], self.param_stats['max'], 'forward')
            elif self.param_type == 'standardization':
                return self.standardize(sample, self.param_stats['mean'], self.param_stats['std'], 'forward')
            elif self.param_type == 'identity':
                return self.identity(sample, 'forward')
        elif type == 'values':
            if self.value_type == 'normalization':
                return self.normalize(sample, self.value_stats['min'], self.value_stats['max'], 'forward')
            elif self.value_type == 'standardization':
                return self.standardize(sample, self.value_stats['mean'], self.value_stats['std'], 'forward')
            elif self.value_type == 'identity':
                return self.identity(sample, 'forward')



    def inverse_transform(self, sample, type):
        ''' perform inverse transformation
        '''
        # make sure this sample is 2d array
        assert len(sample.shape)==2

        if type == 'params':
            if self.param_type == 'normalization':
                return self.normalize(sample, self.param_stats['min'], self.param_stats['max'], 'forward')
            elif self.param_type == 'standardization':
                return self.standardize(sample, self.param_stats['mean'], self.param_stats['std'], 'forward')
            elif self.param_type == 'identity':
                return self.identity(sample, 'reverse')
        elif type == 'values':
            if self.value_type == 'normalization':
                return self.normalize(sample, self.value_stats['min'], self.value_stats['max'], 'forward')
            elif self.value_type == 'standardization':
                return self.standardize(sample, self.value_stats['mean'], self.value_stats['std'], 'forward')
            elif self.value_type == 'identity':
                return self.identity(sample, 'reverse')
