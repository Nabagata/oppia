# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for open feedback threads continuous computations."""

from core import jobs_registry
from core.domain import event_services
from core.domain import feedback_jobs
from core.platform import models
(feedback_models,) = models.Registry.import_models([models.NAMES.feedback])
from core.tests import test_utils
import feconf


class ModifiedOpenFeedbacksAggregator(feedback_jobs.OpenFeedbacksStatisticsAggregator):
    """A modified OpenFeedbacksStatisticsAggregator that does not start a new batch
    job when the previous one has finished.
    """
    @classmethod
    def _get_batch_job_manager_class(cls):
        return ModifiedOpenFeedbacksMRJobManager

    @classmethod
    def _kickoff_batch_job_after_previous_one_ends(cls):
        pass


class ModifiedOpenFeedbacksMRJobManager(feedback_jobs.OpenFeedbacksMRJobManager):

    @classmethod
    def _get_continuous_computation_class(cls):
        return ModifiedOpenFeedbacksStatisticsAggregator


class OpenFeedbaksAggregatorUnitTests(test_utils.GenericTestBase):
    """Tests for statistics aggregations."""

    ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS = [
        ModifiedOpenFeedbacksAggregator]

    def test_multiple_threads_open(self):
        with self.swap(
                jobs_registry, 'ALL_CONTINUOUS_COMPUTATION_MANAGERS',
                self.ALL_CONTINUOUS_COMPUTATION_MANAGERS_FOR_TESTS):
            # Create test objects.
            exp_id = 'eid'
            thread_id_1 = 'tid1'
            thread_id_2 = 'tid2'
            self.save_new_valid_exploration(exp_id, 'owner')
            thread_1= feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_1)
            thread_1.exploration_id = exp_id
            thread_1.put()
            thread_2 = feedback_models.FeedbackThreadModel.create(
                exp_id, thread_id_2)
            thread_2.exploration_id = exp_id          
            thread_2.put()
           
            self.process_and_flush_pending_tasks()
            ModifiedOpenFeedbacksAggregator.start_computation()
            self.assertEqual(self.count_jobs_in_taskqueue(), 1)
            self.process_and_flush_pending_tasks()

            output_model = feedback_models.OpenFeedbacksModel.get(exp_id)
            self.assertEqual(output_model.num_of_open_feedbacks, 2)
