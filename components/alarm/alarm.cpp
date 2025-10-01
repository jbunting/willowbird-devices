// alarm.cpp
#include "alarm.h"
#include "esphome/core/log.h"

namespace esphome {
namespace alarm {

static const char *const TAG = "alarm";

void Alarm::setup() {
  if (!this->time_) return;

  // Schedule daily alarm
  this->time_->add_on_time({.hour = this->alarm_hour_, .minute = this->alarm_minute_}, [this](time::ESPTime) {
    this->trigger_alarm_();
  });
}

void Alarm::trigger_alarm_() {
  if (this->condition_ && !this->condition_()) return;

  ESP_LOGI(TAG, "Alarm triggered");
  if (this->rtttl_) {
    this->rtttl_->play(this->sequence_);
    this->playing_ = true;
    this->snoozed_ = false;
    this->set_active_state_(true, false);
  }
}

void Alarm::stop() {
  if (this->playing_ && this->rtttl_) {
    this->rtttl_->stop();
  }
  this->cancel_timeout("snooze");  // cancel pending snooze
  this->playing_ = false;
  this->snoozed_ = false;
  this->set_active_state_(false, false);
  ESP_LOGI(TAG, "Alarm stopped");
}

void Alarm::snooze(uint32_t ms) {
  if (!this->playing_) return;

  if (this->rtttl_) this->rtttl_->stop();
  this->playing_ = false;
  this->snoozed_ = true;
  this->set_active_state_(true, true);

  // schedule retrigger
  this->set_timeout("snooze", ms, [this]() {
    this->trigger_alarm_();
  });
  ESP_LOGI(TAG, "Alarm snoozed for %u ms", ms);
}

void Alarm::unsnooze() {
  if (!this->snoozed_) return;

  this->cancel_timeout("snooze");
  this->trigger_alarm_();  // will set playing=true, snoozed=false
  ESP_LOGI(TAG, "Alarm unsnoozed immediately");
}

void Alarm::set_active_state_(bool playing, bool snoozed) {
  if (this->active_sensor)
    this->active_sensor->publish_state(playing || snoozed);
  if (this->snoozed_sensor)
    this->snoozed_sensor->publish_state(snoozed);
}

}  // namespace alarm
}  // namespace esphome
